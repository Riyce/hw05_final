from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    list = Post.objects.all()
    paginator = Paginator(list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    list = group.posts.all()
    paginator = Paginator(list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    list = author.posts.all()
    paginator = Paginator(list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if User.objects.filter(username=request.user.username).exists():
        if Follow.objects.filter(user=request.user, author=author).exists():
            following = True
    return render(
        request,
        'profile.html',
        {
            'author': author,
            'page': page,
            'paginator': paginator,
            'following': following,
        }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    following = False
    if User.objects.filter(username=request.user.username).exists():
        if Follow.objects.filter(user=request.user, author=author).exists():
            following = True
    return render(
        request,
        'post.html',
        {
            'post': post,
            'author': author,
            'form': form,
            'comments': comments,
            'following': following,
        }
    )


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    if request.user != author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
                request.POST or None,
                files=request.FILES or None,
                instance=post
            )
    if form.is_valid():
        form.save()
        return redirect(
            'post',
            username=username,
            post_id=post_id
        )
    return render(
        request,
        'new.html',
        {'form': PostForm(instance=post), 'post': post}
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
        return redirect(
            'post',
            username=username,
            post_id=post_id,
        )
    return render(request, 'includes/comments.html', {'form': form})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    follow = request.user.follower.all()
    list = Post.objects.filter(author__in=follow.values('author').all())
    paginator = Paginator(list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    follow_user = get_object_or_404(User, username=username)
    if request.user != follow_user:
        Follow.objects.get_or_create(user=request.user, author=follow_user)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    unfollow_user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=unfollow_user).delete()
    return redirect('profile', username=username)
