# Eventro Requirements


## 1. Overview
Eventro is an event management application where admins and hosts can create events, hosts can add venues and schedule shows, and customers can browse events and book show tickets. Admins and hosts can block or unblock venues and shows.


## 2. Roles and Access
- Roles: `admin`, `host`, `customer`.
- Authorization is enforced by role and user identity(email id and user id).

## 3. Core User Flows 
- Sign up as a customer 
- Log in with valid credentials and stay authenticated across protected screens.
- Log in with invalid credentials and receive a clear error message.

## 4. User Profile and Bookings
- Customer can view only their own profile.
- Customer can view only their own bookings list.
- Booked tickets can be downloaded as a PDF

## 5. Events
- Admin/host can create an event with valid inputs.
- Event category options: `movie`, `workshop`, `party`.
- Customer sees only non-blocked events.
- Admin can view and filter blocked events.
- Admin can block or unblock an event.

## 6. Venues
- Host can add a venue.
- Host can moderate or delete only their own venues.

## 7. Shows
- Host can create a show for an event only on their active venues.
- Customers can only view show details for active shows.
- Shows listing supports filtering by event and city; optional date.
- Host can view only their own shows.
- Admin/host can block or unblock a show.

## 8. Bookings
- Customer can book seats for an active show.
- Booking fails if any selected seat is already booked.
- Booking fails if show, event, or venue is blocked.
- Admin can book on behalf of a user (by email).






