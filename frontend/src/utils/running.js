export function haversineMeters(pointA, pointB) {
  const earthRadius = 6371000
  const toRadians = (value) => (value * Math.PI) / 180
  const latitudeDelta = toRadians(pointB.latitude - pointA.latitude)
  const longitudeDelta = toRadians(pointB.longitude - pointA.longitude)
  const latitudeA = toRadians(pointA.latitude)
  const latitudeB = toRadians(pointB.latitude)

  const value =
    Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(latitudeA)
      * Math.cos(latitudeB)
      * Math.sin(longitudeDelta / 2) ** 2
  return 2 * earthRadius * Math.asin(Math.sqrt(value))
}

export function calculateDistanceKm(points) {
  if (points.length < 2) return 0
  const meters = points.slice(1).reduce(
    (total, point, index) => total + haversineMeters(points[index], point),
    0,
  )
  return Math.round((meters / 1000) * 100) / 100
}

export function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60
  return [hours, minutes, remainingSeconds]
    .map((value) => String(value).padStart(2, '0'))
    .join(':')
}

export function formatPace(paceSeconds) {
  if (!paceSeconds || !Number.isFinite(paceSeconds)) return `--'--"`
  const minutes = Math.floor(paceSeconds / 60)
  const seconds = Math.round(paceSeconds % 60)
  return `${minutes}'${String(seconds).padStart(2, '0')}"`
}
