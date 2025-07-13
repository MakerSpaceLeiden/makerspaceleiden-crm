class VolunteeringReminderNotification(object):
    def __init__(self, user, event):
        self.user = user
        self.event = event

    def get_text(self):
        chore_description = self.event.chore.description
        chore_event_ts_human = self.event.ts.strftime("%a %d/%m/%Y %H:%M")
        return f"{self.user.first_name}, here's a friendly reminder that you signed up for {chore_description} at {chore_event_ts_human}. Don't forget!"

    def get_subject_for_email(self):
        return "Volunteering reminder"
