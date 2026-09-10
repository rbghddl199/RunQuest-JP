let kakaoMapPromise = null
let loadedKakao = null
const KAKAO_MAP_SDK_ID = 'kakao-map-sdk'

export function loadKakaoMap() {
  if (loadedKakao) return Promise.resolve(loadedKakao)

  if (window.kakao?.maps) {
    return new Promise((resolve) => {
      window.kakao.maps.load(() => {
        loadedKakao = window.kakao
        resolve(loadedKakao)
      })
    })
  }

  if (kakaoMapPromise) return kakaoMapPromise

  const appKey = import.meta.env.VITE_KAKAO_MAP_APP_KEY
  if (!appKey) {
    return Promise.reject(new Error('Kakao Maps JavaScript key is missing.'))
  }

  kakaoMapPromise = new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      kakaoMapPromise = null
      reject(new Error('Kakao Maps SDK loading timed out.'))
    }, 9000)

    const resolveLoaded = () => {
      if (!window.kakao?.maps) {
        window.clearTimeout(timeoutId)
        kakaoMapPromise = null
        reject(new Error('Kakao Maps SDK is not available.'))
        return
      }
      window.kakao.maps.load(() => {
        window.clearTimeout(timeoutId)
        loadedKakao = window.kakao
        resolve(loadedKakao)
      })
    }

    const existingScript = document.querySelector(`#${KAKAO_MAP_SDK_ID}`)
    if (existingScript) {
      if (window.kakao?.maps) {
        resolveLoaded()
        return
      }
      if (existingScript.dataset.loaded === 'true' || existingScript.dataset.failed === 'true') {
        existingScript.remove()
      } else {
        existingScript.addEventListener('load', resolveLoaded, { once: true })
        existingScript.addEventListener('error', () => {
          existingScript.dataset.failed = 'true'
          window.clearTimeout(timeoutId)
          kakaoMapPromise = null
          reject(new Error('Kakao Maps SDK could not be loaded.'))
        }, { once: true })
        return
      }
    }

    if (window.kakao?.maps) {
      resolveLoaded()
      return
    }

    const script = document.createElement('script')
    script.id = KAKAO_MAP_SDK_ID
    script.dataset.kakaoMapSdk = 'true'
    script.async = true
    script.defer = true
    script.fetchPriority = 'high'
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&autoload=false&libraries=services`
    script.onload = () => {
      script.dataset.loaded = 'true'
      resolveLoaded()
    }
    script.onerror = () => {
      script.dataset.failed = 'true'
      window.clearTimeout(timeoutId)
      kakaoMapPromise = null
      reject(new Error('Kakao Maps SDK could not be loaded.'))
    }
    document.head.appendChild(script)
  })

  return kakaoMapPromise
}

export function preloadKakaoMap() {
  const warmUp = () => {
    loadKakaoMap().catch(() => {})
  }

  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(warmUp, { timeout: 1200 })
    return
  }

  window.setTimeout(warmUp, 300)
}
