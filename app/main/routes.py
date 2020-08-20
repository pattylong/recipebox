from flask import request, jsonify, abort, render_template, flash, redirect, url_for, current_app, g
from flask_login import current_user, login_required
from datetime import datetime
from app import db
from app.main.forms import EditProfileForm, EmptyForm, RecipeForm, SearchForm
from app.models import User, Recipe, Tag
from app.main import bp


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.search_form = SearchForm()


"""
###############################################################
#########################   ROUTES   ##########################
###############################################################
"""


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def home():
    #return "hello"
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(user_id=current_user.id, name=form.name.data,
                        instructions=form.instructions.data,
                        ingredients=form.ingredients.data)
        db.session.add(recipe)
        db.session.commit()
        flash('Your recipe has been created.')
        return redirect(url_for('main.home'))
    if not current_user.is_anonymous:
        page = request.args.get('page', 1, type=int)
        recipes = current_user.followed_recipes().paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('main.home', page=recipes.next_num) \
            if recipes.has_next else None
        prev_url = url_for('main.home', page=recipes.prev_num) \
            if recipes.has_prev else None
        return render_template('index.html', title='Home Page', form=form, recipes=recipes.items,
                           next_url=next_url, prev_url=prev_url)
    return render_template('index.html', title='Home Page', form=form)


@bp.route('/search')
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    recipes, total = Recipe.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', recipes=recipes, next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
def user_popup(username):
    user = User.query.filter_by(name=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/users', methods=['GET'])
@login_required
def get_all_users():
    data = []
    users = db.session.query(User.id, User.name).all()
    if not users:
        return "There are currently no users."
    for user in users:
        data.append({
            "id": user.id,
            "name": user.name
        })

    result = {"data": data,
              "success": True}

    return jsonify(result)



@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.name)
    if form.validate_on_submit():
        current_user.name = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.name
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(name=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    recipes = user.recipes.order_by(Recipe.created_time.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.name, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('main.user', username=user.name, page=recipes.prev_num) \
        if recipes.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, recipes=recipes.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/explore')
def explore():
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.order_by(Recipe.created_time.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('main.explore', page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template('index.html', title='Explore', recipes=recipes.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/users', methods=['POST'])
def add_user():
    return None


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.home'))
        if user == current_user:
            flash('You cannot follow yourself.')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are now following {}'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.home'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.home'))
        if user == current_user:
            flash('You cannot unfollow yourself.')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You have unfollowed {}.'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.home'))


@bp.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe_with_id(recipe_id):
    recipe = db.session.query(Recipe).filter_by(id=recipe_id).first()
    if not recipe:
        abort(404)
    return render_template('recipe_full.html', recipe=recipe)


"""
### ~~~~~~~~ API ~~~~~~~~~ ###

@bp.route('/recipes', methods=['GET'])
def get_all_recipes():
    data = []
    recipes = db.session.query(Recipe).order_by(Recipe.name).all()
    if not recipes:
        return "You currently have no recipes."
    for recipe in recipes:
        data.append({
            "id": recipe.id,
            "user_id": recipe.user_id,
            "name": recipe.name,
            "tags": recipe.tag
        })

    result = {"data": data,
              "success": True}

    return jsonify(result)


@bp.route('/tags', methods=['GET'])
def get_all_tags():
    data = []
    tags = db.session.query(Tag).order_by(Tag.name).all()
    if not tags:
        abort(404)
    for tag in tags:
        data.append({
            "id": tag.id,
            "name": tag.name
        })

    result = {"data": data,
              "success": True}

    return jsonify(result)


@bp.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe_with_id(recipe_id):
    recipe = db.session.query(Recipe).filter_by(id=recipe_id).first()
    if not recipe:
        abort(404)
    data = {
        "id": recipe.id,
        "user_id": recipe.user_id,
        "name": recipe.name,
        "instructions": recipe.instructions,
        "ingredients": recipe.ingredients,
        "recipe_link": recipe.recipe_link,
        "tags": recipe.tags
    }

    result = {"data": data,
              "success": True}

    return jsonify(result)


@bp.route('/users/<int:user_id>/recipes', methods=['GET'])
def get_user_recipes(user_id):
    recipes = db.session.query(User.recipes).filter_by(id=user_id).all()
    if not recipes:
        abort(404)
    data = []
    for recipe in recipes:
        data.append({
            "id": recipe.id,
            "user_id": recipe.user_id,
            "name": recipe.name,
            "tags": recipe.tags
        })

    result = {"data": data,
              "success": True}

    return jsonify(result)


@bp.route('/tags/<int:tag_id>/recipes', methods=['GET'])
def get_tag_recipes(tag_id):
    recipes = db.session.query(Tag.recipes).filter_by(id=tag_id).all()
    if not recipes:
        abort(404)
    data = []
    for recipe in recipes:
        data.append({
            "id": recipe.id,
            "user_id": recipe.user_id,
            "name": recipe.name,
            "tags": recipe.tags
        })

    result = {"data": data,
              "success": True}

    return jsonify(result)



"""

