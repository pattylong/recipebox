from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length
from app.models import User


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(name=self.username.data).first()
            if user is not None:
                raise ValidationError('Username taken. Please use a different username.')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class RecipeForm(FlaskForm):
    # name, instructions, ingredients, recipe_link, and tags
    name = StringField('Recipe Name', validators=[DataRequired()])
    instructions = StringField('Instructions', validators=[DataRequired()])
    ingredients = StringField('Ingredients', validators=[DataRequired()])
    # tags - some type of list
    submit = SubmitField('Submit')



