# alembic revision --autogenerate -m "..."
# alembic upgrade head

Create a profile for organizers where people with events or attendees could look, communicate or hire organizers.
It will also be a marketing opportunity for the organizers.
Need to include profile pictures static directory


https://chatgpt.com/c/69263e04-76e0-8327-a88b-f0b564a05c21


Implement get ticket instance by seat number functionality in ticket instance service and repository layers.

There are many API calls that return data that is not being used in the frontend. Consider not returning unneeded data to optimize performance and reduce payload size. I need just to return 204 status code for certain delete and update operations instead of returning the entire object not being used in the frontend. Have user-related endpoints revamped first.

Moreover, if certain fields are not used in the frontend, modify the service and repository layers to exclude those fields from the response. This will help streamline data transfer and improve efficiency.

Work on user email verification functionality in the backend (service layer). Implement email token generation, sending verification emails, and verifying tokens when users click on the verification link.

Work on the logout functionality in the frontend to ensure that JWT tokens are properly deleted from client storage upon logout.