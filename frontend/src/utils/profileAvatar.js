const PROFILE_AVATAR_PREFIX = 'runquest_profile_avatar:'

function avatarKey(userKey) {
  return `${PROFILE_AVATAR_PREFIX}${userKey || 'default'}`
}

export function getStoredProfileAvatar(userKey) {
  return localStorage.getItem(avatarKey(userKey))
}

export function clearStoredProfileAvatar(userKey) {
  localStorage.removeItem(avatarKey(userKey))
}

export function saveStoredProfileAvatar(userKey, dataUrl) {
  localStorage.setItem(avatarKey(userKey), dataUrl)
}

export function fileToProfileAvatar(file, size = 256) {
  return new Promise((resolve, reject) => {
    if (!file?.type?.startsWith('image/')) {
      reject(new Error('이미지 파일을 선택해 주세요.'))
      return
    }

    const reader = new FileReader()
    reader.onerror = () => reject(new Error('이미지를 불러오지 못했습니다.'))
    reader.onload = () => {
      const image = new Image()
      image.onerror = () => reject(new Error('이미지를 처리하지 못했습니다.'))
      image.onload = () => {
        const canvas = document.createElement('canvas')
        canvas.width = size
        canvas.height = size
        const ctx = canvas.getContext('2d')
        const crop = Math.min(image.width, image.height)
        const sx = (image.width - crop) / 2
        const sy = (image.height - crop) / 2
        ctx.drawImage(image, sx, sy, crop, crop, 0, 0, size, size)
        resolve(canvas.toDataURL('image/jpeg', 0.86))
      }
      image.src = reader.result
    }
    reader.readAsDataURL(file)
  })
}
