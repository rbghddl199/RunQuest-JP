import json
import os
from collections import defaultdict
from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Course, FavoriteCourse, RecommendationSession, RunningRecord
from core.recommendations import (
    build_record_profile,
    combine_scores,
    diversify_ranked_courses,
    location_fit,
    ordered_records,
    record_fit,
    records_after_latest_gap,
    resolve_weights,
    safety_fit,
    survey_fit,
)


@contextmanager
def temporary_env(name, value):
    original = os.environ.get(name)
    os.environ[name] = str(value)
    try:
        yield
    finally:
        if original is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = original


class Command(BaseCommand):
    help = 'Evaluate recommendation quality by cohort and location weight.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--weights',
            default='0,0.35,0.45,0.55,0.65',
            help='Comma-separated location weights to evaluate.',
        )
        parser.add_argument('--latitude', type=float, default=36.3504)
        parser.add_argument('--longitude', type=float, default=127.3845)

    def handle(self, *args, **options):
        weights = [
            float(item.strip())
            for item in options['weights'].split(',')
            if item.strip()
        ]
        users = (
            get_user_model().objects
            .filter(survey_response__isnull=False)
            .select_related('survey_response', 'profile')
        )
        courses = list(Course.objects.filter(is_active=True))
        output = {
            'metric_definitions': {
                'hit_rate': 'Top-1 course matches preferred type and target distance tolerance.',
                're_recommendation_rate': 'Top-1 course was already shown in the user latest recommendation sessions.',
                'favorite_conversion_rate': 'Top-7 candidates include a course the user saved.',
            },
            'datasets': {},
            'experiments': [],
        }

        for location_weight in weights:
            rows = []
            with temporary_env('RECOMMENDATION_LOCATION_WEIGHT', location_weight):
                for user in users:
                    records = list(
                        RunningRecord.objects.filter(
                            user=user,
                            status=RunningRecord.Status.COMPLETED,
                        )
                        .select_related('course')
                        .order_by('-completed_at')
                    )
                    weights_for_user = resolve_weights(records)
                    cohort = self.cohort_name(weights_for_user)
                    profile_records = (
                        ordered_records(records_after_latest_gap(records))[:20]
                        if weights_for_user.user_state == 'returning'
                        and records_after_latest_gap(records)
                        else ordered_records(records)[:20]
                    )
                    record_profile = build_record_profile(profile_records)
                    ranked = self.rank_courses(
                        courses,
                        user.survey_response,
                        record_profile,
                        weights_for_user,
                        options['latitude'],
                        options['longitude'],
                        location_weight > 0,
                    )
                    if not ranked:
                        continue
                    top_course = ranked[0]['course']
                    top7_ids = {item['course'].id for item in ranked[:7]}
                    previous_ids = set(
                        RecommendationSession.objects.filter(user=user)
                        .order_by('-created_at')
                        .values_list('items__course_id', flat=True)[:21]
                    )
                    favorite_ids = set(
                        FavoriteCourse.objects.filter(user=user)
                        .values_list('course_id', flat=True)
                    )
                    rows.append(
                        {
                            'cohort': cohort,
                            'hit': self.is_hit(top_course, user.survey_response),
                            're_recommended': top_course.id in previous_ids,
                            'favorite_converted': bool(top7_ids & favorite_ids),
                        }
                    )

            output['experiments'].append(
                {
                    'location_weight': location_weight,
                    'summary': self.summarize(rows),
                }
            )
            for cohort, count in self.dataset_counts(rows).items():
                output['datasets'][cohort] = max(
                    output['datasets'].get(cohort, 0),
                    count,
                )

        self.stdout.write(json.dumps(output, ensure_ascii=False, indent=2))

    def cohort_name(self, weights):
        if weights.user_state == 'new':
            return 'new'
        if weights.user_state == 'active':
            return 'active'
        if weights.returning_recent_count:
            return 'returning_adapting'
        return 'returning'

    def rank_courses(
        self,
        courses,
        survey,
        record_profile,
        weights,
        latitude,
        longitude,
        location_applied,
    ):
        ranked = []
        for course in courses:
            survey_score, _ = survey_fit(course, survey)
            record_score, _ = record_fit(course, record_profile)
            safety_score = safety_fit(
                course,
                survey,
                record_profile,
                weights.user_state,
            )
            personalized_score = (
                survey_score * weights.survey
                + record_score * weights.record
                + safety_score * weights.safety
            )
            location_score, _ = location_fit(course, latitude, longitude)
            total_score = combine_scores(
                personalized_score,
                location_score,
                course.popularity_score,
                location_applied,
            )
            ranked.append({'course': course, 'total_score': total_score})
        return diversify_ranked_courses(
            sorted(ranked, key=lambda item: item['total_score'], reverse=True),
            limit=7,
        )

    def is_hit(self, course, survey):
        profile = survey.score_profile
        preferred_types = set(profile['preferred_course_types'])
        target_distance = float(profile['target_distance_km'])
        distance_gap = abs(float(course.distance_km) - target_distance)
        return (
            course.course_type in preferred_types
            and distance_gap <= max(1.5, target_distance * 0.35)
        )

    def dataset_counts(self, rows):
        counts = defaultdict(int)
        for row in rows:
            counts[row['cohort']] += 1
        return dict(counts)

    def summarize(self, rows):
        counts = self.dataset_counts(rows)
        summary = {}
        for cohort in sorted(counts):
            cohort_rows = [row for row in rows if row['cohort'] == cohort]
            count = len(cohort_rows)
            summary[cohort] = {
                'count': count,
                'hit_rate': self.rate(cohort_rows, 'hit'),
                're_recommendation_rate': self.rate(cohort_rows, 're_recommended'),
                'favorite_conversion_rate': self.rate(cohort_rows, 'favorite_converted'),
            }
        return summary

    def rate(self, rows, key):
        if not rows:
            return 0
        return round(sum(1 for row in rows if row[key]) / len(rows), 3)
