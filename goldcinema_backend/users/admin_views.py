from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib import messages
import os
from django.conf import settings

from .models import Movie, Booking, CustomUser
from .forms import MovieForm


# --- Helper: Allow only admin users ---
def is_admin(user):
    return user.is_superuser


# ================================
# ADMIN DASHBOARD HOME
# ================================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):

    total_users = CustomUser.objects.count()
    total_bookings = Booking.objects.count()

    # Recent bookings
    recent_bookings = Booking.objects.order_by("-created_at")[:8]

    # Build chart data
    from django.db.models import Count
    chart_data = (
        Booking.objects.values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    chart_dates = [entry["date"].strftime("%Y-%m-%d") for entry in chart_data]
    chart_counts = [entry["count"] for entry in chart_data]

    # Popular movies
    popular_movies = (
        Booking.objects.values("movie_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Calculate total revenue
    total_revenue = 0
    all_bookings = Booking.objects.all()
    for b in all_bookings:
        m = Movie.objects.filter(title=b.movie_name).first()
        if m:
            seat_count = len(b.seats.split(","))
            total_revenue += m.price * seat_count

    return render(request, "admin/dashboard.html", {
        "total_users": total_users,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
        "recent_bookings": recent_bookings,
        "popular_movies": popular_movies,
        "chart_dates": chart_dates,
        "chart_counts": chart_counts,
    })


# ================================
# ADMIN — USERS TABLE
# ================================
@login_required
@user_passes_test(is_admin)
def admin_users(request):

    search = request.GET.get("q", "")

    users = CustomUser.objects.all().order_by("id")

    if search:
        users = users.filter(email__icontains=search)

    paginator = Paginator(users, 10)
    page = request.GET.get("page")
    users_page = paginator.get_page(page)

    return render(request, "admin/users.html", {
        "users": users_page,
        "search_query": search,
    })


# ================================
# DELETE USER (ADMIN)
# ================================
@login_required
@user_passes_test(is_admin)
def delete_user_admin(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if user.is_superuser:
        messages.error(request, "⚠️ You cannot delete super admin accounts.")
        return redirect("admin_users")

    user.delete()
    messages.success(request, "✔ User deleted successfully.")
    return redirect("admin_users")


# ================================
# ADMIN — BOOKINGS TABLE
# ================================
@login_required
@user_passes_test(is_admin)
def admin_bookings(request):

    bookings = Booking.objects.all().order_by("-created_at")
    paginator = Paginator(bookings, 12)
    page = request.GET.get("page")
    bookings_page = paginator.get_page(page)

    return render(request, "admin/bookings.html", {
        "bookings": bookings_page
    })


# ================================
# DELETE BOOKING
# ================================
@login_required
@user_passes_test(is_admin)
def delete_booking_admin(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)
    booking.delete()

    messages.success(request, "✔ Booking deleted successfully.")
    return redirect("admin_bookings")


@login_required
@user_passes_test(is_admin)
def cancel_booking(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)
    booking.delete()

    messages.success(request, "✔ Booking cancelled successfully.")
    return redirect("admin_bookings")


# ================================
# MOVIES MANAGEMENT
# ================================
@login_required
@user_passes_test(is_admin)
def admin_movies(request):

    q = request.GET.get("q", "")
    movies_qs = Movie.objects.all().order_by("-id")

    if q:
        movies_qs = movies_qs.filter(title__icontains=q)

    paginator = Paginator(movies_qs, 20)
    page = request.GET.get("page")
    movies_page = paginator.get_page(page)

    return render(request, "admin/admin_movies.html", {
        "movies": movies_page,
        "q": q
    })


@login_required
@user_passes_test(is_admin)
def admin_movie_add(request):
    if request.method == "POST":
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✔ Movie added.")
            return redirect("admin_movies")
    else:
        form = MovieForm()

    return render(request, "admin/admin_movie_form.html", {
        "form": form,
        "action": "Add Movie"
    })


@login_required
@user_passes_test(is_admin)
def admin_movie_edit(request, movie_id):

    movie = get_object_or_404(Movie, id=movie_id)
    old_poster = movie.poster.path if movie.poster else None

    if request.method == "POST":
        form = MovieForm(request.POST, request.FILES, instance=movie)

        if form.is_valid():
            if "poster" in request.FILES and old_poster:
                try:
                    if os.path.exists(old_poster):
                        os.remove(old_poster)
                except:
                    pass

            form.save()
            messages.success(request, "✔ Movie updated.")
            return redirect("admin_movies")

    else:
        form = MovieForm(instance=movie)

    return render(request, "admin/admin_movie_form.html", {
        "form": form,
        "action": "Edit Movie",
        "movie": movie
    })


@login_required
@user_passes_test(is_admin)
def admin_movie_delete(request, movie_id):

    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":

        if movie.poster and movie.poster.path:
            try:
                if os.path.exists(movie.poster.path):
                    os.remove(movie.poster.path)
            except:
                pass

        movie.delete()
        messages.success(request, "✔ Movie deleted.")
        return redirect("admin_movies")

    return render(request, "admin/admin_confirm_delete.html", {
        "object": movie,
        "cancel_url": "admin_movies",
        "confirm_text": f"Delete movie '{movie.title}'?"
    })


# ================================
# ADMIN USER DETAIL PAGE
# ================================
@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):

    user = get_object_or_404(CustomUser, id=user_id)
    bookings = Booking.objects.filter(user=user).order_by("-created_at")

    return render(request, "admin/admin_user_detail.html", {
        "user_obj": user,
        "bookings": bookings,
    })

