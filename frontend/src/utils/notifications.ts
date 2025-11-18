interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: Date
  read: boolean
}

class NotificationCenter {
  private listeners: ((notifications: Notification[]) => void)[] = []
  private notifications: Notification[] = []

  subscribe(listener: (notifications: Notification[]) => void) {
    this.listeners.push(listener)
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener)
    }
  }

  private notify() {
    this.listeners.forEach(listener => listener([...this.notifications]))
  }

  add(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false
    }
    this.notifications.unshift(newNotification)
    if (this.notifications.length > 50) this.notifications = this.notifications.slice(0, 50)
    this.notify()
  }

  markAsRead(id: string) {
    const notification = this.notifications.find(n => n.id === id)
    if (notification) {
      notification.read = true
      this.notify()
    }
  }

  clear() {
    this.notifications = []
    this.notify()
  }

  getAll() {
    return [...this.notifications]
  }

  getUnreadCount() {
    return this.notifications.filter(n => !n.read).length
  }
}

export const notifications = new NotificationCenter()

// Auto-generate notifications for bot events
export const initBotNotifications = () => {
  // Success notifications
  const notifySuccess = (title: string, message: string) => {
    notifications.add({ type: 'success', title, message })
  }

  // Error notifications
  const notifyError = (title: string, message: string) => {
    notifications.add({ type: 'error', title, message })
  }

  // Info notifications
  const notifyInfo = (title: string, message: string) => {
    notifications.add({ type: 'info', title, message })
  }

  return { notifySuccess, notifyError, notifyInfo }
}