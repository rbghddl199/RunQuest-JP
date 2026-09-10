export function formatDistance(kilometers, unit = 'km', digits = 1) {
  const value = Number(kilometers || 0)
  if (unit === 'mi') {
    return `${(value * 0.621371).toFixed(digits)}mi`
  }
  return `${value.toFixed(digits)}km`
}

export function formatTemperature(celsius, unit = 'c') {
  const value = Number(celsius || 0)
  if (unit === 'f') {
    return `${Math.round((value * 9) / 5 + 32)}°F`
  }
  return `${Math.round(value)}°C`
}

export function formatWindSpeed(kilometersPerHour, unit = 'km') {
  const value = Number(kilometersPerHour || 0)
  return unit === 'mi'
    ? `${(value * 0.621371).toFixed(1)}mph`
    : `${value.toFixed(1)}km/h`
}

export function convertDistance(kilometers, unit = 'km') {
  const value = Number(kilometers || 0)
  return unit === 'mi' ? value * 0.621371 : value
}

export function convertPaceSeconds(secondsPerKilometer, unit = 'km') {
  const value = Number(secondsPerKilometer || 0)
  return unit === 'mi' ? Math.round(value * 1.609344) : value
}

export function paceUnit(unit = 'km') {
  return unit === 'mi' ? '/mi' : '/km'
}
