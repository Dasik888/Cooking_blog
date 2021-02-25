
from flask import Flask, session
from flask import render_template, abort, request, redirect
from recipes import models
import re

app = Flask(__name__)
app.secret_key = 'some_secret_key'


def get_current_user():
    return {
        'is_authorized': session.get('is_authorized'),
        'user_info': session.get('user_data')
    }

def get_recipe_in_favourite(id, user_id):
    recipes = models.Recipes.get_favourites(user_id)
    for one_recipe in recipes:
        if one_recipe['id'] == id:
            return {'in_favourite': True}
    return {'in_favourite': False}


def validate_email(email):
    template = '^[a-zA-Z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if re.match(template, email):
        return True
    else:
        return False

def validate_pass(password):
    min_lenght = 5
    if len(password) < min_lenght:
        return False
    else:
        return True


@app.route('/', methods=['GET', 'POST'])
@app.route('/Home page', methods=['GET', 'POST'])
def menu():
    categories = models.Category.get_all()
    recipes = models.Recipes.get_some()
    if not session.get('is_authorized'):
        if request.method == 'POST':
            form_data = dict(request.form)
            mail = form_data['login']
            password = form_data['password']
            user_data = models.User.find_by_mail_password(
                mail=mail,
                password=password
            )
            if user_data:
                session['is_authorized'] = True
                session['user_data'] = user_data
                message = request.args.get('message')
                return render_template('menu.html', title='Home Page', categories=categories, recipes=recipes, message=message, user_info=get_current_user(), user_id=user_data['id'])
            else:
                return redirect('/Home page?message=User_not_found')
        else:
            return render_template('menu.html', title='Home Page', categories=categories, recipes=recipes, user_info=get_current_user())
    else:
        if request.method == 'POST':
            form_data = dict(request.form)
            if form_data['logout'] == 'Log out':
                del session['user_data']
                session['is_authorized'] = False
                return redirect('/')
        user_data = session.get('user_data')
        user_id = user_data['id']
        count = models.Favourite.get_count_favourites(user_id)
        return render_template('menu.html', title='Home Page', categories=categories, recipes=recipes,
                               user_info=get_current_user(), user_id=user_data['id'], count=count)


@app.route('/<category_name>', methods=['GET', 'POST'])
def category(category_name):
    categories = models.Category.get_all()
    recipes = models.Recipes.get_by_category(category_name)
    if not session.get('is_authorized'):
        return render_template('category.html', title=category_name, recipes=recipes, categories=categories,
                               user_info=get_current_user(), category_name=category_name)
    else:
        user_data = session.get('user_data')
        user_id = user_data['id']
        count = models.Favourite.get_count_favourites(user_id)
        return render_template('category.html', title=category_name, recipes=recipes, categories=categories,
                               user_info=get_current_user(), user_id=user_data['id'], count=count,
                               category_name=category_name)


@app.route('/recipe/<int:id>', methods=['GET', 'POST'])
def recipe(id):
    categories = models.Category.get_all()
    recipe = models.Recipes.get_by_id(id)
    list_ingredients = recipe['ingredients'].split('\n')
    list_of_steps = recipe['steps'].split('\n')
    if not session.get('is_authorized'):
        return render_template('recipe.html', title=recipe['name'], recipe=recipe, categories=categories,
                                user_info=get_current_user(), ingredients=list_ingredients, steps=list_of_steps,
                               category_name=recipe['category'])
    else:
        user_data = session.get('user_data')
        user_id = user_data['id']
        recipe_info = get_recipe_in_favourite(id, user_id)
        count = models.Favourite.get_count_favourites(user_id)
        if request.method == 'POST':
            if recipe_info['in_favourite']:
                models.Favourite.delete_by_id(id, user_id)
                return redirect('/recipe/{}'.format(id))
            else:
                models.Favourite.add_by_id(id, user_id)
                return redirect('/recipe/{}'.format(id))
        return render_template('recipe.html', title=recipe['name'], recipe=recipe, categories=categories,
                               user_info=get_current_user(), user_id=user_id, ingredients=list_ingredients,
                               steps=list_of_steps, recipe_info=recipe_info, count=count, category_name=recipe['category'])


@app.route('/cooking_book/<int:user_id>')
def favourite(user_id):
    categories = models.Category.get_all()
    user_data = session.get('user_data')
    current_user_id = user_data['id']
    if not session.get('is_authorized'):
        return redirect('/Home page')
    elif user_id != current_user_id:
        del session['user_data']
        session['is_authorized'] = False
        return redirect('/Home page?message=User_not_authorized')
    else:
        recipes = models.Recipes.get_favourites(user_id)
        count = models.Favourite.get_count_favourites(user_id)
        return render_template('favourite.html', title='Cooking book', recipes=recipes, categories=categories,
                               user_info=get_current_user(), count=count)


@app.route('/registration', methods=['GET', 'POST'])
def register():
    categories = models.Category.get_all()
    if request.method == 'POST':
        form_data = dict(request.form)
        mail = form_data['login']
        password = form_data['password']
        name = form_data['name']
        valid_email = validate_email(mail)
        valid_pass = validate_pass(password)
        if valid_email and valid_pass:
            models.User.add_new(mail, password, name)
            return redirect('/Home page')
        elif not valid_email:
            return redirect('/registration?message=Invalid_email')
        elif not valid_pass:
            return redirect('/registration?message=Incorrect_password')
    return render_template('register.html', title='Registration', categories=categories, user_info=get_current_user())


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

