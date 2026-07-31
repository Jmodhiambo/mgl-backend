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
        ├── templates.py                          # All organizer template classes
        ├── branded_message.html                  # Generic wrapper — every bulk-send
        │                                          # template (named or custom) renders
        │                                          # through this one file now
        ├── co_organizer_invitation_existing.html
        ├── co_organizer_invitation_new_user.html
        ├── event_created.html
        ├── event_approved.html
        ├── event_rejected.html
        ├── event_pending_deletion.html
        ├── event_deletion_confirmed.html
        ├── ticket_type_suspended.html
        └── ticket_type_unsuspended.html
```

> The six named bulk-send templates (`reminder`, `update`, `thank_you`,
> `cancellation`, `venue_change`, `time_change`) and `custom` no longer have
> their own `.html` files — see "Organizer bulk-send emails" below. All the
> other organizer templates (co-organizer invitations, event lifecycle
> notices, ticket type suspension) are unaffected — still one fixed `.html`
> file each, rendered via `send_from_template()` exactly as before.

---

## 🗑️ Files to DELETE

### Original cleanup (SendGrid → Resend migration)

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

### Branded-message consolidation (superseded by `branded_message.html`)

```bash
rm app/emails/templates/organizer/booking_reminder.html
rm app/emails/templates/organizer/event_update.html
rm app/emails/templates/organizer/thank_you.html
rm app/emails/templates/organizer/event_cancellation.html
rm app/emails/templates/organizer/venue_change.html
rm app/emails/templates/organizer/time_change.html
rm app/emails/templates/organizer/custom_email.html
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

### Header colour: two mechanisms now

**Fixed templates** (user/admin account emails, organizer system emails like
event approval or co-organizer invitations) still set their header colour at
*template-definition* time — each `.html` file overrides
`{% block header_class %}green{% endblock %}` directly:

```css
.header.teal {
    background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
}
```

**Organizer bulk-send templates** (the six named presets plus `custom`) set
their header colour at *render* time instead, since they all share the one
`branded_message.html` file. `header_class`/`header_subtitle` are declared as
plain fields on each preset's `EmailTemplate` class in `organizer/templates.py`
and passed into the Jinja render as variables:

```html
{% block header_class %}{{ header_class }}{% endblock %}
{% block header_subtitle %}{{ header_subtitle }}{% endblock %}
```

Available header colours (either mechanism): `green`, `blue`, `red`, `purple`,
`amber`, `pink` (default is orange/red — omit to use it).

### Organizer bulk-send emails: branded wrapper, free text

This is the biggest structural change. Previously, the six named templates
(`reminder`, `update`, `thank_you`, `cancellation`, `venue_change`,
`time_change`) each had their own fixed `.html` file with structured content
(info-boxes, tables) built from booking variables — and critically, whatever
subject/body an organizer typed into the send-email modal for a *named*
template was silently discarded; only `extra_variables` (e.g.
`cancellation_reason`) actually reached the sent email.

That's gone. Now:

- **One render path for every bulk-send template.** `reminder`, `update`,
  `thank_you`, `cancellation`, `venue_change`, `time_change`, and `custom` all
  render through `organizer/branded_message.html` via
  `EmailManager.send_branded_message()` / `render_branded_message()`. Subject
  and body are always the organizer's own text — nothing is discarded.
- **`template_used` now only selects two things:** the header colour/subtitle
  (via the preset's `header_class`/`header_subtitle`, or a fixed default for
  `custom`), and which `extra_variables` are required before sending (see
  `_EXTRA_REQUIRED` in `organizer_emails_services.py` — unchanged from before,
  e.g. `cancellation` still requires `cancellation_reason` and `total_price`).
- **Per-recipient personalisation is preserved via `{{token}}` substitution.**
  The organizer's subject/body can contain tokens like `{{customer_name}}`,
  `{{order_id}}`, `{{ticket_type}}`, `{{quantity}}`, `{{venue}}`,
  `{{event_date}}`, `{{organizer_name}}`, `{{total_price}}`, plus whatever
  `extra_variables` were supplied. `_substitute_tokens()` fills these in per
  booking at send time — mirrors the frontend's `fillTokens()` in
  `BookingsView.tsx` exactly (same `{{key}}` syntax, unmatched tokens left
  as-is).
- **Selecting a template in the UI only pre-fills a starting draft.** The
  `EMAIL_TEMPLATES` array in `BookingsView.tsx` still has default
  subject/body copy per preset, purely as a convenience starting point —
  it's not authoritative and isn't rendered by the backend. Organizers can
  edit freely from there.
- **Preview is the real thing, not a lookalike.** `render_branded_message()`
  is the one function both the preview endpoint and the actual send path
  call — given the same subject/body/branding inputs, preview returns
  byte-for-byte what would be sent.
- **Booking lookups are scoped to the calling organizer.**
  `booking_repo.get_enriched_bookings_by_ids_repo()` now takes an optional
  `organizer_id` — both `send_bulk_email_service` and `preview_email_service`
  pass their caller's id, so a `booking_id` belonging to another organizer's
  event is excluded from the query results and surfaces as a plain 404
  rather than leaking whether it exists.

### Template classes are thin

Each template class holds only:
- Metadata (`id`, `name`, `category`, `description`, `required_variables`)
- `template_file` path pointing to its `.html` file (for organizer bulk-send
  presets, this is always `"organizer/branded_message.html"`)
- `header_class` / `header_subtitle` — branding metadata, `None` for fixed
  templates that set their header colour directly in their own `.html` file
- `get_subject()` — the subject line, optionally using variables (only
  actually called for fixed templates now — bulk-send subjects come from
  the organizer)

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

### Send a templated email (fixed templates — user/admin/system)

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

### Send an organizer bulk-send email (branded wrapper, free text)

```python
await email_manager.send_branded_message(
    to_email="attendee@example.com",
    subject="Quick update about tomorrow",
    body="Hi there, just a heads up that...",
    header_class="amber",
    header_subtitle="Important Event Update",
)
```

In practice this is always called from `organizer_emails_services.py`, which
resolves `header_class`/`header_subtitle` from `template_used` and
personalises subject/body per recipient first — see
`send_bulk_email_service()`.

### Preview an organizer bulk-send email before sending

```python
html = email_manager.render_branded_message(
    subject="Reminder: {{event_title}} is Coming Up!",
    body="Dear {{customer_name}}, ...",
    header_class="blue",
    header_subtitle="Your event is coming up soon!",
)
```

Exposed to the frontend as `POST /organizers/me/emails/preview` — same
`SendEmailRequest`-shaped payload as `/emails/send`, but targeting a single
`booking_id` and never writing any log/recipient rows.

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

### Organizer bulk-send presets (`organizer/templates.py`)

Subject/body columns below are **default starting drafts only** — organizers
can edit both freely before sending; what actually goes out is their edited
text, personalised per recipient. `template_used` only determines the header
colour/subtitle and which extra variables are required.

| `template_used` | Header             | Default subject draft                    | Required `extra_variables`              |
|------------------|--------------------|-------------------------------------------|------------------------------------------|
| `reminder`       | blue               | Reminder: {event_title} is Coming Up!     | —                                        |
| `update`         | amber              | Important Update: {event_title}           | `update_message`                         |
| `thank_you`      | green              | Thank You for Attending {event_title}!    | —                                        |
| `cancellation`   | red                | Important: {event_title} Has Been Cancelled | `cancellation_reason`, `total_price`   |
| `venue_change`   | purple             | Venue Change: {event_title}               | `old_venue`, `new_venue`                 |
| `time_change`    | pink               | Time Change: {event_title}                | `old_date_time`, `new_date_time`         |
| `custom`         | blue (fixed)       | — (organizer writes their own)            | —                                        |

Base tokens available in subject/body for every preset (resolved per booking
automatically, no `extra_variables` needed): `customer_name`, `order_id`,
`event_title`, `ticket_type`, `quantity`, `venue`, `event_date`,
`organizer_name`, `total_price`.

### Organizer system templates (fixed HTML, unaffected by the above)

| ID                                          | Subject                                              | Required variables |
|----------------------------------------------|-------------------------------------------------------|---------------------|
| `organizer.co_organizer_invitation`           | You've Been Invited to Co-Organise: {event_title}      | `recipient_name`, `inviter_name`, `event_title`, `venue`, `event_date`, `accept_url` |
| `organizer.co_organizer_invitation_new_user`  | You're Invited to Co-Organise: {event_title} on MGLTickets | `recipient_name`, `inviter_name`, `event_title`, `venue`, `event_date`, `signup_url` |
| `organizer.event_created`                     | Event Submitted: {event_title} is Under Review         | `organizer_name`, `event_title`, `venue`, `event_date`, `dashboard_url` |
| `organizer.event_approved`                    | 🎉 Your Event Has Been Approved: {event_title}          | `organizer_name`, `event_title`, `venue`, `event_date`, `admin_name`, `event_url` |
| `organizer.event_rejected`                    | Event Submission Not Approved: {event_title}            | `organizer_name`, `event_title`, `admin_name`, `dashboard_url` |
| `organizer.event_pending_deletion`            | Action Required: {event_title} is Pending Deletion       | `organizer_name`, `event_title`, `unresolved_count` |
| `organizer.event_deletion_confirmed`          | Event Permanently Deleted: {event_title}                | `organizer_name`, `event_title`, `deleted_at`, `refund_count`, `dashboard_url` |
| `organizer.ticket_type_suspended`             | Ticket Type Suspended: {ticket_type_name} – {event_title} | `organizer_name`, `event_title`, `ticket_type_name`, `admin_name`, `suspension_reason` |
| `organizer.ticket_type_unsuspended`           | Suspension Lifted: {ticket_type_name} – {event_title}   | `organizer_name`, `event_title`, `ticket_type_name`, `dashboard_url` |

> This table (and the co-organizer invitation split into "existing user" vs
> "new user" variants above) reflects what's actually registered in
> `organizer/templates.py`. It was out of sync with the previous version of
> this doc even before the branded-message change — worth a periodic
> re-check against the actual template classes rather than trusting this
> table blindly as the codebase grows.

---

## 🔌 API Endpoints (organizer bulk-send)

### `POST /organizers/me/emails/preview`

Renders exactly what `/emails/send` would dispatch for one representative
booking. Never sends anything, never writes a log/recipient row.

```json
{
  "booking_id": 4821,
  "template_used": "cancellation",
  "subject": "Important: {{event_title}} Has Been Cancelled",
  "body": "Dear {{customer_name}}, ...",
  "extra_variables": { "cancellation_reason": "Venue double-booked", "total_price": "4500" }
}
```

→ `{ "subject": "...", "html": "..." }`

### `POST /organizers/me/emails/send`

Same shape, plus `booking_ids` (list) instead of `booking_id`. `subject` and
`body` are required for every `template_used`, including named presets —
this is the change from the old API, where they were silently ignored
outside of `custom`.

Both endpoints 404 if any referenced booking doesn't belong to one of the
calling organizer's own events.

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
|--------------------------------------------------|------------------------------|--------------------------------------|
| `handle_mpesa_callback_service` — success path   | `organizer.reminder` (queued for day-before send) or a new `user.order_confirmed` template | `order_id`, `event_title`, `ticket_type`, `quantity` |
| Free order fast-path in `initiate_mpesa_payment_service` | Same as above       | Same                                 |

---

## ➕ Adding a new template

### Fixed template (user/admin/organizer system emails)

**1. Create the HTML file**

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

**2. Add the class to the role templates file**

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

**3. Register it in the registry**

```python
# In template_registry.py _register_all()

from app.emails.templates.user.templates import (
    ...,
    MyNewTemplate,
)

# Add to the list:
MyNewTemplate(),
```

**4. Use it**

```python
await email_manager.send_from_template(
    template_id="user.my_new",
    to_email="user@example.com",
    variables={"name": "Jane", "some_url": "https://..."},
)
```

### Organizer bulk-send preset

No new HTML file needed — every preset shares `branded_message.html`.

**1. Add the class to `organizer/templates.py`**

```python
class RefundIssuedTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.refund_issued",
            name="Refund Issued",
            category="organizer",
            description="Sent when a refund has been processed for an attendee",
            required_variables=[
                "customer_name", "event_title", "ticket_type",
                "quantity", "order_id", "refund_amount", "organizer_name",
            ],
            template_file="organizer/branded_message.html",
            header_class="green",
            header_subtitle="Refund Confirmation",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Refund Issued: {variables['event_title']}"
```

**2. Register it in `template_registry.py`** — same as the fixed-template flow.

**3. If it needs a required extra field** (like `cancellation_reason`), add
it to `_EXTRA_REQUIRED` in `organizer_emails_services.py`:

```python
_EXTRA_REQUIRED = {
    ...,
    "refund_issued": ["refund_amount"],
}
```

**4. Add it to `_VALID_TEMPLATES`** in the same file, and to the
`EMAIL_TEMPLATES` array in `BookingsView.tsx` with a default draft
subject/body and any `extraFields` UI inputs it needs.

That's it — no HTML file, no changes to `EmailManager`, no changes to the
send/preview endpoints. The new preset is usable immediately.