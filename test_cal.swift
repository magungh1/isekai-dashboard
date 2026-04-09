import EventKit

let store = EKEventStore()
store.requestAccess(to: .event) { (granted, error) in
    if granted {
        print("Access granted")
    } else {
        print("Access denied: \(String(describing: error))")
    }
}
RunLoop.main.run(until: Date(timeIntervalSinceNow: 2.0))
