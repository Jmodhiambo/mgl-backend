# Email System — Implementation Package

## 📁 Final File Structure

```
app/emails/
├── base.py                           # BaseEmailService (ABC)
├── email_service.py                  # EmailService(BaseEmailService) — Resend
├── email_manager.py                  # Central manager (singleton)
│
└── templates/
    ├── base_email.html               # Shared layout (header, footer, CSS)
    ├── email_template_base.py        # EmailTemplate dataclass ABC
    ├── template_registry.py          # Registers and indexes all templates
    │
    ├── user/
    │   ├── templates.py              # All user template classes
    │   ├── verification_email.html
    │   ├── password_reset.html
    │   └── account_reactivation.html
    │
    └── organizer/
        ├── templates.py              # All organizer template classes
        ├── booking_reminder.html
        ├── event_update.html
        ├── thank_you.html
        ├── event_cancellation.html
        ├── venue_change.html
        ├── time_change.html
        ├── co_organizer_invitation.html
        └── custom_email.html
```

---

## 🗑️ Files to DELETE

These were replaced by the new structure:

```bash
rm app/emails/sendgrid_service.py
rm app/emails/templates/user/verification_email.py
rm app/emails/templates/user/password_reset.py
rm app/emails/templates/user/account_reactivation.py
rm app/emails/templates/organizer/booking_reminder.py
rm app/emails/templates/organizer/event_update.py
rm app/emails/templates/organizer/thank_you.py
rm app/emails/templates/organizer/event_cancellation.py
rm app/emails/templates/organizer/venue_change.py
rm app/emails/templates/organizer/time_change.py
rm app/emails/templates/organizer/co_organizer_invitation.py
```

---

## 📦 Dependencies

Install on server:

```bash
pip install resend premailer --break-system-packages
```

---

## ⚙️ Environment Variables

All email config is provider-agnostic. Update your `.env` files:

| Old key (SendGrid)           | New key (generic)        |
|------------------------------|--------------------------|
| `SENDGRID_API_KEY`           | `EMAIL_API_KEY`          |
| `SENDGRID_NO_REPLY_EMAIL`    | `EMAIL_FROM_NO_REPLY`    |
| `SENDGRID_SUPPORT_EMAIL`     | `EMAIL_FROM_SUPPORT`     |
| `SENDGRID_BILLING_EMAIL`     | `EMAIL_FROM_BILLING`     |
| `SENDGRID_PRESS_EMAIL`       | `EMAIL_FROM_PRESS`       |
| `SENDGRID_PARTNERSHIP_EMAIL` | `EMAIL_FROM_PARTNERSHIP` |
| `SENDGRID_FROM_NAME`         | `EMAIL_FROM_NAME`        |

**New variable:**

| Key              | Values           | Notes                                                                 |
|------------------|------------------|-----------------------------------------------------------------------|
| `EMAIL_DEV_MODE` | `true` / `false` | `true` by default — logs instead of sending. Set `false` in `.env.production`. |

**.env example:**

```env
EMAIL_API_KEY=re_xxxxxxxxxxxxxxxx
EMAIL_FROM_NO_REPLY=no-reply@mgltickets.com
EMAIL_FROM_SUPPORT=support@mgltickets.com
EMAIL_FROM_BILLING=billing@mgltickets.com
EMAIL_FROM_PRESS=press@mgltickets.com
EMAIL_FROM_PARTNERSHIP=partnership@mgltickets.com
EMAIL_FROM_NAME=MGLTickets
EMAIL_DEV_MODE=true
```

---

## 🏗️ Architecture Decisions

### Provider-agnostic by design

The ABC in `base.py` (`BaseEmailService`) defines the interface. The concrete
implementation in `email_service.py` (`EmailService`) currently uses Resend.

To switch providers:
1. Replace the body of `EmailService.send_email` with the new provider's SDK call
2. Update `EMAIL_API_KEY` in your `.env`
3. Nothing else changes — `EmailManager`, templates, and all call sites stay untouched

### Jinja2 + premailer

Templates are `.html` files rendered via Jinja2's `Environment`. After rendering,
`premailer.transform()` converts `<style>` block CSS to inline `style` attributes
so Gmail, Outlook, and Apple Mail all render the design correctly.

### Header colour via CSS modifier classes

Each child template overrides `{% block header_class %}` with a colour name
(`green`, `blue`, `red`, `purple`, `amber`, `pink`). The base layout applies
this as a CSS class on the `.header` div. This keeps Jinja2 out of `style`
attributes, eliminating CSS linter errors in VS Code.

To add a new header colour, add one CSS rule to `base_email.html`:
```css
.header.teal {
    background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
}
```
Then use `{% block header_class %}teal{% endblock %}` in the child template.

### Template classes are thin

Each template class holds only:
- Metadata (`id`, `name`, `category`, `description`, `required_variables`)
- `template_file` path pointing to its `.html` file
- `get_subject()` — the subject line, optionally using variables

All rendering logic lives in `EmailManager`. Templates never touch HTML directly.

### One file per role

Template classes are grouped by role rather than split one-per-file:

- `user/templates.py` — all user email classes
- `organizer/templates.py` — all organizer email classes
- `admin/templates.py` — admin email classes (when needed)

### Order hierarchy alignment

The platform hierarchy is `Order → Booking → TicketInstance`.

- **Order** — the customer-facing reference (`order_id`). Shown in all emails.
- **Booking** — internal line item (one per ticket type within an order). Not exposed in emails.
- **TicketInstance** — individual tickets with a `code` (e.g. `TKT-{booking_id}-{UUID}`). Presented at the gate.

All organizer email templates reference `order_id`, not `booking_id`. The label
in email bodies reads "Order #{{ order_id }}" so customers can reference it
when contacting support.

### Dev mode

`EMAIL_DEV_MODE=true` (default) causes `EmailManager` to log the rendered HTML
instead of calling the provider. Safe for local development — no credentials
needed, no send quota consumed. Check `app/logs/app.jsonl` to inspect output.

---

## 🚀 Usage

### Send a templated email

```python
from app.emails.email_manager import email_manager

await email_manager.send_from_template(
    template_id="user.verification",
    to_email="user@example.com",
    variables={
        "name": "John Doe",
        "verification_url": "https://mgltickets.com/verify?token=abc123",
    },
)
```

### Send a custom freeform email (organizers)

```python
await email_manager.send_custom(
    to_email="attendee@example.com",
    subject="Quick update about tomorrow",
    body="Hi there, just a heads up that...",
    organizer_name="Events by Wanjiku",
)
```

### List available templates

```python
# All templates
email_manager.list_templates()

# By role
email_manager.list_templates(category="organizer")

# Single template info
email_manager.get_template_info("organizer.reminder")
```

---

## 📋 Template Reference

### User templates (`user/templates.py`)

| ID                           | Subject                                          | Required variables             |
|------------------------------|--------------------------------------------------|--------------------------------|
| `user.verification`          | Verify Your MGLTickets Account                   | `name`, `verification_url`     |
| `user.password_reset`        | Reset Your MGLTickets Password                   | `name`, `reset_url`            |
| `user.account_reactivation`  | Your MGLTickets Account Has Been Reactivated     | `name`, `login_url`            |

### Organizer templates (`organizer/templates.py`)

| ID                                  | Subject                                        | Required variables |
|-------------------------------------|------------------------------------------------|--------------------|
| `organizer.reminder`                | Reminder: {event_title} is Coming Up!          | `customer_name`, `event_title`, `ticket_type`, `quantity`, `order_id`, `venue`, `event_date`, `organizer_name` |
| `organizer.update`                  | Important Update: {event_title}                | `customer_name`, `event_title`, `ticket_type`, `quantity`, `order_id`, `update_message`, `organizer_name` |
| `organizer.thank_you`               | Thank You for Attending {event_title}!         | `customer_name`, `event_title`, `organizer_name` |
| `organizer.cancellation`            | Important: {event_title} Has Been Cancelled    | `customer_name`, `event_title`, `ticket_type`, `quantity`, `order_id`, `total_price`, `cancellation_reason`, `organizer_name` |
| `organizer.venue_change`            | Venue Change: {event_title}                    | `customer_name`, `event_title`, `ticket_type`, `quantity`, `order_id`, `old_venue`, `new_venue`, `event_date`, `organizer_name` |
| `organizer.time_change`             | Time Change: {event_title}                     | `customer_name`, `event_title`, `ticket_type`, `quantity`, `order_id`, `old_date_time`, `new_date_time`, `venue`, `organizer_name` |
| `organizer.co_organizer_invitation` | You've Been Invited to Co-Organise: {event_title} | `recipient_name`, `inviter_name`, `event_title`, `event_id`, `activation_url` |

---

## 🔌 Wiring into services

Email calls are written but commented out in service files, consistent with the
dummy-data pattern used across the codebase. Flip them live by uncommenting.

### user_services.py call sites

| Service function                      | Template ID                   |
|---------------------------------------|-------------------------------|
| `register_user_service`               | `user.verification`           |
| `update_user_info_service`            | `user.verification`           |
| `resend_verification_email_service`   | `user.verification`           |
| `change_user_password_service`        | `user.password_reset`         |
| `request_password_reset_service`      | `user.password_reset`         |
| `reset_password_with_token_service`   | `user.password_reset`         |
| `reactivate_account_service`          | `user.account_reactivation`   |

### payment_services.py — future call sites

These are not yet wired but are the natural trigger points for order-related emails:

| Trigger                                          | Suggested template           | Key variables to pass               |
|--------------------------------------------------|------------------------------|-------------------------------------|
| `handle_mpesa_callback_service` — success path   | `organizer.reminder` (queued for day-before send) or a new `user.order_confirmed` template | `order_id`, `event_title`, `ticket_type`, `quantity` |
| Free order fast-path in `initiate_mpesa_payment_service` | Same as above       | Same                                |

---

## ➕ Adding a new template

### 1. Create the HTML file

```
app/emails/templates/<role>/<template_name>.html
```

Extend the base layout:

```html
{% extends "base_email.html" %}

{% block title %}Your Title – MGLTickets{% endblock %}
{% block header_class %}blue{% endblock %}

{% block content %}
<h2>Hello {{ name }}!</h2>
<p>Your message here.</p>
{% endblock %}
```

Available header colours: `green`, `blue`, `red`, `purple`, `amber`, `pink`
(default is orange/red — omit the block to use it).

### 2. Add the class to the role templates file

```python
# In app/emails/templates/<role>/templates.py

class MyNewTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.my_new",
            name="My New Email",
            category="user",
            description="Sent when something happens",
            required_variables=["name", "some_url"],
            template_file="user/my_new_template.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Something happened, {variables['name']}!"
```

### 3. Register it in the registry

```python
# In template_registry.py _register_all()

from app.emails.templates.user.templates import (
    ...,
    MyNewTemplate,
)

# Add to the list:
MyNewTemplate(),
```

### 4. Use it

```python
await email_manager.send_from_template(
    template_id="user.my_new",
    to_email="user@example.com",
    variables={"name": "Jane", "some_url": "https://..."},
)
```