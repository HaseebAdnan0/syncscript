/**
 * Notification Sound Utility
 * Plays a notification sound when toasts appear, respecting user preferences
 */

const SOUND_FILE_PATH = "/sounds/notification.mp3"
const SOUND_PREFERENCE_KEY = "notification-sound-enabled"

let audioInstance: HTMLAudioElement | null = null

/**
 * Initialize audio instance (lazy loaded)
 */
function getAudioInstance(): HTMLAudioElement {
  if (!audioInstance && typeof window !== "undefined") {
    audioInstance = new Audio(SOUND_FILE_PATH)
    audioInstance.volume = 0.5 // 50% volume to avoid being too loud
  }
  return audioInstance!
}

/**
 * Check if sound is enabled in user preferences (from localStorage)
 */
export function isSoundEnabled(): boolean {
  if (typeof window === "undefined") return false

  const preference = localStorage.getItem(SOUND_PREFERENCE_KEY)
  // Default to true if not set
  return preference === null || preference === "true"
}

/**
 * Check if the current tab is visible
 * Prevents playing sound when user is on another tab
 */
function isTabVisible(): boolean {
  if (typeof document === "undefined") return false
  return !document.hidden
}

/**
 * Play notification sound if:
 * 1. Sound is enabled in preferences
 * 2. Tab is currently visible
 * 3. Browser supports Audio API
 */
export function playNotificationSound(): void {
  // Check all conditions before playing
  if (!isSoundEnabled()) {
    return
  }

  if (!isTabVisible()) {
    return
  }

  if (typeof window === "undefined" || typeof Audio === "undefined") {
    return
  }

  try {
    const audio = getAudioInstance()
    // Reset to start in case it's already playing
    audio.currentTime = 0
    // Play and catch any errors (e.g., user hasn't interacted with page yet)
    audio.play().catch((error) => {
      // Silently fail - browser may block autoplay
      console.debug("Could not play notification sound:", error)
    })
  } catch (error) {
    // Silently fail if audio playback fails
    console.debug("Notification sound error:", error)
  }
}

/**
 * Preload the audio file to reduce latency on first play
 * Call this on app initialization or user interaction
 */
export function preloadNotificationSound(): void {
  if (typeof window === "undefined") return

  try {
    const audio = getAudioInstance()
    audio.load()
  } catch (error) {
    console.debug("Could not preload notification sound:", error)
  }
}
