# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncDate

from urllib.parse import unquote

from .models import CustomUser, Movie, Booking, Notification


# ============================================================
# AUTHENTICATION
# ============================================================

def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")
        city = request.POST.get("city")
        address = request.POST.get("address")
        zip_code = request.POST.get("zip_code")
        phone = request.POST.get("phone")

        if password != confirm_password:
            messages.error(request, "❌ Passwords do not match.")
            return redirect("register")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "⚠️ Email already registered.")
            return redirect("register")

        CustomUser.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            city=city,
            address=address,
            zip_code=zip_code,
            phone=phone,
        )

        messages.success(request, "✅ Registration successful!")
        return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, "✔ Login successful!")

            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect("homepage")

        messages.error(request, "❌ Incorrect email or password")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ============================================================
# HOMEPAGE / DASHBOARD
# ============================================================

@login_required
def homepage(request):
    # Filter movies by category
    all_movies = Movie.objects.all().order_by("-id")
    
    # Case-insensitive filtering for robustness
    movies_list = all_movies.filter(category__iexact="Movie")
    concerts_list = all_movies.filter(category__iexact="Concert")
    plays_list = all_movies.filter(category__iexact="Play") # Or "Plays" depending on admin input, using "Play" as per previous context

    # Also support "Plays" plural if that's what's being saved
    if not plays_list.exists():
         plays_list = all_movies.filter(category__iexact="Plays")

    user_bookings = Booking.objects.filter(user=request.user).order_by("-created_at")

    bookings_json = [
        {
            "movie_name": b.movie_name,
            "date": b.date.strftime("%Y-%m-%d"),
            "time": b.time,
            "seats": b.seats,
            "id": b.id,
        }
        for b in user_bookings
    ]

    return render(request, "homepage.html", {
        "movies": movies_list,
        "concerts": concerts_list,
        "plays": plays_list,
        "bookings": bookings_json,
        "user": request.user,
    })


@login_required
def dashboard_view(request):
    return redirect("homepage")


# ============================================================
# BOOKINGS — CLIENT SIDE
# ============================================================

@login_required
def book_movie_page(request, movie_name):
    # decode movie name in case URL contains %20 etc.
    movie_name = unquote(movie_name)

    # Fallback data for hardcoded movies (if not in DB)
    # In a real app, these should all be in the DB.
    hardcoded_movies = {
        "Taylor Swift Concert Show": {
            "genre": "Concert",
            "duration": "1h 30m",
            "description": "Experience the Eras Tour concert film. A once-in-a-lifetime cultural phenomenon.",
            "poster": "/static/images/tailor.jpg"
        },
        "Free Rock Concert": {
            "genre": "Concert",
            "duration": "1h 55m",
            "description": "Enjoy a night of electrifying rock music for free!",
            "poster": "/static/images/freerock-concert.jpg"
        },
        "A Minecraft Movie": {
            "genre": "Thriller",
            "duration": "2h 10m",
            "description": "The blocky world comes to life in this thrilling adventure.",
            "poster": "/static/images/minecraft.jpg"
        },
        "Echoes of Light": {
            "genre": "Drama",
            "duration": "1h 55m",
            "description": "A touching story about finding hope in the darkest of times.",
            "poster": "https://m.media-amazon.com/images/I/91kFYg4fX3L._AC_UF894,1000_QL80_.jpg"
        },
        "Cold Play": {
            "genre": "Play",
            "duration": "2h 10m",
            "description": "A dramatic play that will keep you on the edge of your seat.",
            "poster": "/static/images/coldplay.jpg"
        },
        "Childs Play": {
            "genre": "Drama",
            "duration": "1h 55m",
            "description": "A gripping drama about childhood innocence and its loss.",
            "poster": "/static/images/childsplay.jpg"
        },
        "Other Movies": {
            "genre": "Various",
            "duration": "Varies",
            "description": "Explore a wide variety of other movies and shows available at Gold Cinema.",
            "poster": "/static/images/other-movies.jpg"
        }
    }

    context = {
        "movie_name": movie_name,
    }

    # Try to find in DB
    movie_obj = Movie.objects.filter(title=movie_name).first()
    
    if movie_obj:
        context["movie_genre"] = movie_obj.genre if movie_obj.genre else movie_obj.category
        context["movie_duration"] = f"{movie_obj.duration} mins" if movie_obj.duration else None
        context["movie_description"] = movie_obj.description if movie_obj.description else "Experience this amazing title at Gold Cinema. Book your tickets now!"
        context["movie_price"] = movie_obj.price
        if movie_obj.poster:
            context["movie_poster"] = movie_obj.poster.url
    elif movie_name in hardcoded_movies:
        data = hardcoded_movies[movie_name]
        context["movie_genre"] = data["genre"]
        context["movie_duration"] = data["duration"]
        context["movie_description"] = data["description"]
        context["movie_poster"] = data["poster"]
        # Fallback price if not in DB (though we populated it, good to have safety)
        context["movie_price"] = 1000 
    
    # We no longer pass booked_seats here because the modal fetches them via API
    # based on selected date/time.

    return render(request, "movie_details.html", context)


@login_required
def create_booking(request):
    if request.method == "POST":
        # Decode movie name
        movie_encoded = request.POST.get("movie_name")
        movie = unquote(movie_encoded)

        date = request.POST.get("date")
        time = request.POST.get("time")
        raw_seats = request.POST.get("selected_seats", "").strip()

        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts("application/json")

        # Validate seats
        if not raw_seats:
            msg = "⚠️ Please select at least one seat."
            if is_ajax:
                return JsonResponse({"success": False, "message": msg})
            messages.error(request, msg)
            return redirect(f"/book/{movie}/")

        seats = ",".join([s.strip() for s in raw_seats.split(",")])
        seat_list = [s.strip() for s in seats.split(",")]

        # Check for existing booked seats
        existing = Booking.objects.filter(
            movie_name=movie,
            date=date,
            time=time
        )

        already_booked = []
        for b in existing:
            already_booked.extend([s.strip() for s in b.seats.split(",")])

        conflict_seats = [s for s in seat_list if s in already_booked]

        if conflict_seats:
            msg = f"❌ Seat(s) already booked: {', '.join(conflict_seats)}"
            if is_ajax:
                return JsonResponse({"success": False, "message": msg})
            messages.error(request, msg)
            return redirect(f"/book/{movie}/")

        # Check Balance & Deduct Price
        movie_obj = Movie.objects.filter(title=movie).first()
        price = movie_obj.price if movie_obj else 0
        
        # If multiple seats, multiply price? Usually per seat.
        # Assuming price is per seat.
        total_cost = price * len(seat_list)

        if request.user.balance < total_cost:
            msg = f"❌ Insufficient funds. Cost: KSH {total_cost}, Balance: KSH {request.user.balance}"
            if is_ajax:
                return JsonResponse({"success": False, "message": msg, "error_type": "insufficient_funds"})
            messages.error(request, msg)
            return redirect(f"/book/{movie}/")

        # Deduct balance
        request.user.balance -= total_cost
        request.user.save()

        # SAVE BOOKING
        Booking.objects.create(
            user=request.user,
            movie_name=movie,
            date=date,
            time=time,
            seats=seats
        )

        # CREATE NOTIFICATION
        Notification.objects.create(
            user=request.user,
            message=f"Booking confirmed for {movie} on {date} at {time}. Seats: {seats}",
            notification_type="booking_success"
        )

        success_msg = f"Booking successful! 🎉 KSH {total_cost} deducted."
        if is_ajax:
            return JsonResponse({"success": True, "message": success_msg, "new_balance": request.user.balance})

        messages.success(request, success_msg)
        return redirect("homepage")

    return redirect("homepage")


@login_required
def cancel_my_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if request.method == "POST":
        # Calculate refund
        movie = Movie.objects.filter(title=booking.movie_name).first()
        refund_amount = 0
        
        if movie:
            # Count seats (assuming comma-separated)
            seats_list = [s for s in booking.seats.split(",") if s.strip()]
            seat_count = len(seats_list)
            refund_amount = movie.price * seat_count
            
            # Credit user balance
            request.user.balance += refund_amount
            request.user.save()

        booking.delete()
        messages.success(request, f"Booking cancelled. KSH {refund_amount} has been refunded to your account. 🗑️")
        return redirect("homepage")
        
    return redirect("homepage")


# API — return JSON booked seats
@login_required
def get_booked_seats(request, movie_name):
    movie_name = unquote(movie_name)

    date = request.GET.get("date")
    time = request.GET.get("time")

    seats = []

    if date and time:
        bookings = Booking.objects.filter(movie_name=movie_name, date=date, time=time)
        for b in bookings:
            seats.extend(s.strip() for s in b.seats.split(","))

    return JsonResponse({"booked_seats": seats})


@login_required
def get_user_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by("-created_at")

    booking_list = [{
        "movie": b.movie_name,
        "date": b.date.strftime("%Y-%m-%d"),
        "time": b.time,
        "seats": b.seats,
        "bookingId": b.id
    } for b in bookings]

    return JsonResponse({"bookings": booking_list})


# ============================================================
# ACCOUNT
# ============================================================

@login_required
def account_view(request):
    return render(request, "account.html", {"user": request.user})


@login_required
def update_account(request):
    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.city = request.POST.get("city")
        user.address = request.POST.get("address")
        user.zip_code = request.POST.get("zip_code")
        user.phone = request.POST.get("phone")
        user.save()

        messages.success(request, "✔ Profile updated successfully!")
        return redirect("account")

    return render(request, "update_account.html", {"user": user})


@login_required
def delete_account_view(request):
    user = request.user
    logout(request)
    user.delete()
    return redirect("register")


from decimal import Decimal

@login_required
def deposit_view(request):
    if request.method == "POST":
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts("application/json")
        try:
            amount = Decimal(request.POST.get("amount", 0))
            if amount > 0:
                request.user.balance += amount
                request.user.save()
                msg = f"✅ Successfully deposited KSH {amount}!"
                if is_ajax:
                    return JsonResponse({"success": True, "message": msg, "new_balance": request.user.balance})
                messages.success(request, msg)
            else:
                msg = "⚠️ Invalid amount."
                if is_ajax:
                    return JsonResponse({"success": False, "message": msg})
                messages.error(request, msg)
        except Exception:
            msg = "⚠️ Invalid amount."
            if is_ajax:
                return JsonResponse({"success": False, "message": msg})
            messages.error(request, msg)
        
        return redirect("account")
    
    return render(request, "deposit.html")


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@staff_member_required
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    total_bookings = Booking.objects.count()
    
    # Calculate total revenue (naive approach: sum of all bookings * price of movie)
    # Since we didn't store price at booking time, we use current movie price.
    # For more accuracy, we should have stored price in Booking model, but for now:
    total_revenue = 0
    all_bookings = Booking.objects.all()
    for b in all_bookings:
        m = Movie.objects.filter(title=b.movie_name).first()
        if m:
            # Count seats
            seat_count = len(b.seats.split(","))
            total_revenue += m.price * seat_count

    popular = (
        Booking.objects.values("movie_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    bookings_by_day_qs = (
        Booking.objects.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    dates = [str(x["day"]) for x in bookings_by_day_qs]
    counts = [x["count"] for x in bookings_by_day_qs]

    recent = Booking.objects.select_related("user").order_by("-created_at")[:10]

    context = {
        "total_users": total_users,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
        "popular_movies": list(popular),
        "chart_dates": dates,
        "chart_counts": counts,
        "recent_bookings": recent,
    }

    return render(request, "admin/dashboard.html", context)


@staff_member_required
def admin_users(request):
    q = request.GET.get("q", "")
    users_qs = CustomUser.objects.all().order_by("-date_joined")

    if q:
        users_qs = users_qs.filter(email__icontains=q)

    paginator = Paginator(users_qs, 20)
    page = request.GET.get("page")
    users_page = paginator.get_page(page)

    return render(request, "admin/users.html", {"users": users_page, "q": q})


@staff_member_required
def admin_bookings(request):
    q = request.GET.get("q", "")

    bookings_qs = Booking.objects.select_related("user").order_by("-created_at")

    if q:
        bookings_qs = bookings_qs.filter(movie_name__icontains=q)

    paginator = Paginator(bookings_qs, 25)
    page = request.GET.get("page")
    bookings_page = paginator.get_page(page)

    return render(request, "admin/bookings.html", {"bookings": bookings_page, "q": q})


# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

@login_required
def update_profile(request):
    """Update user profile information"""
    if request.method == "POST":
        try:
            user = request.user
            
            # Get form data
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            email = request.POST.get("email", "").strip()
            phone = request.POST.get("phone", "").strip()
            city = request.POST.get("city", "").strip()
            address = request.POST.get("address", "").strip()
            zip_code = request.POST.get("zip_code", "").strip()
            
            # Validate required fields
            if not first_name or not last_name or not email:
                return JsonResponse({
                    "success": False,
                    "error": "First name, last name, and email are required"
                })
            
            # Check if email is already taken by another user
            if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                return JsonResponse({
                    "success": False,
                    "error": "This email is already registered to another account"
                })
            
            # Update user fields
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = email  # Keep username in sync with email
            user.phone = phone
            user.city = city
            user.address = address
            user.zip_code = zip_code
            
            user.save()
            
            return JsonResponse({
                "success": True,
                "message": "Profile updated successfully"
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"An error occurred: {str(e)}"
            })
    
    return JsonResponse({"success": False, "error": "Invalid request method"})


@login_required
def change_password(request):
    """Change user password"""
    if request.method == "POST":
        try:
            user = request.user
            
            # Get form data
            current_password = request.POST.get("current_password", "")
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")
            
            # Validate all fields are provided
            if not current_password or not new_password or not confirm_password:
                return JsonResponse({
                    "success": False,
                    "error": "All password fields are required"
                })
            
            # Verify current password
            if not user.check_password(current_password):
                return JsonResponse({
                    "success": False,
                    "error": "Current password is incorrect"
                })
            
            # Validate new passwords match
            if new_password != confirm_password:
                return JsonResponse({
                    "success": False,
                    "error": "New passwords do not match"
                })
            
            # Validate password strength (minimum 6 characters)
            if len(new_password) < 6:
                return JsonResponse({
                    "success": False,
                    "error": "Password must be at least 6 characters long"
                })
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Re-authenticate the user to maintain their session
            auth_login(request, user)
            
            return JsonResponse({
                "success": True,
                "message": "Password changed successfully"
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"An error occurred: {str(e)}"
            })
    
    return JsonResponse({"success": False, "error": "Invalid request method"})


@login_required
def delete_account(request):
    """Delete user account permanently"""
    if request.method == "POST":
        try:
            user = request.user
            
            # Get password for confirmation
            password = request.POST.get("password", "")
            
            # Validate password is provided
            if not password:
                return JsonResponse({
                    "success": False,
                    "error": "Password is required to delete your account"
                })
            
            # Verify password
            if not user.check_password(password):
                return JsonResponse({
                    "success": False,
                    "error": "Incorrect password"
                })
            
            # Log the user out
            logout(request)
            
            # Delete the user account (this will also delete related bookings due to CASCADE)
            user.delete()
            
            return JsonResponse({
                "success": True,
                "message": "Account deleted successfully"
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"An error occurred: {str(e)}"
            })
    
    return JsonResponse({"success": False, "error": "Invalid request method"})


# ============================================================
# NOTIFICATIONS
# ============================================================

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    
    data = [{
        "id": n.id,
        "message": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
        "type": n.notification_type
    } for n in notifications]
    
    return JsonResponse({"notifications": data})


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({"success": True})
