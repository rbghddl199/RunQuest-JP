import expoEvening from '../assets/images/courses/expo-evening.webp'
import gapcheonRiver from '../assets/images/courses/gapcheon-river.webp'
import hanbatArboretum from '../assets/images/courses/hanbat-arboretum.webp'

const generatedCourseImages = import.meta.glob(
  '../assets/images/demo/courses/*.webp',
  { eager: true, query: '?url', import: 'default' },
)
const postImages = import.meta.glob(
  '../assets/images/demo/posts/*.webp',
  { eager: true, query: '?url', import: 'default' },
)
const profileImages = import.meta.glob(
  '../assets/images/demo/profiles/*.webp',
  { eager: true, query: '?url', import: 'default' },
)

function filenameKey(path) {
  return path.split('/').pop().replace(/\.[^.]+$/, '')
}

const generatedCourses = Object.fromEntries(
  Object.entries(generatedCourseImages).map(([path, url]) => [filenameKey(path), url]),
)

const courseImages = {
  'expo-evening': generatedCourses['expo-evening'] ?? expoEvening,
  'gapcheon-river': generatedCourses['gapcheon-river'] ?? gapcheonRiver,
  'hanbat-arboretum': generatedCourses['hanbat-arboretum'] ?? hanbatArboretum,
  ...generatedCourses,
}

const courseFallbackKeys = Object.keys(courseImages)
const postImageList = Object.values(postImages)
const profileImageList = Object.values(profileImages)

function stableIndex(seed, length) {
  if (!length) return 0
  const text = String(seed ?? 'runquest')
  let hash = 0
  for (let index = 0; index < text.length; index += 1) {
    hash = (hash * 31 + text.charCodeAt(index)) >>> 0
  }
  return hash % length
}

export function getCourseImage(imageKey, seed = null) {
  if (seed && courseFallbackKeys.length) {
    return courseImages[courseFallbackKeys[stableIndex(`${imageKey}-${seed}`, courseFallbackKeys.length)]]
      ?? hanbatArboretum
  }
  if (imageKey && courseImages[imageKey]) return courseImages[imageKey]
  return courseImages[courseFallbackKeys[stableIndex(imageKey, courseFallbackKeys.length)]]
    ?? hanbatArboretum
}

export function getCourseImageForCourse(course) {
  return getCourseImage(course?.image_key, course?.slug ?? course?.id ?? course?.name)
}

export function getPostImages(post) {
  if (Array.isArray(post?.images) && post.images.length) return post.images.slice(0, 8)
  return []
}

export function getProfileImage(seed) {
  return profileImageList[stableIndex(seed, profileImageList.length)] ?? null
}
