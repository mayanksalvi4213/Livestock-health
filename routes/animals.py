from flask import Blueprint, render_template, session, g, redirect, url_for, request
from models import db, User, Animal, AnimalType, Farm

animals_bp = Blueprint('animals', __name__)

@animals_bp.route('/animals')
def index():
    """Display list of user's animals"""
    # Ensure user is logged in
    if not g.user:
        return redirect(url_for('auth.login'))
    
    # Get user's animals
    animals = Animal.query.filter_by(user_id=g.user.id).all()
    
    # Get animal types for dropdown
    animal_types = AnimalType.query.all()
    
    return render_template('animals/index.html', 
                          animals=animals,
                          animal_types=animal_types)

@animals_bp.route('/animals/<int:animal_id>')
def view_animal(animal_id):
    """Display details for a specific animal"""
    # Ensure user is logged in
    if not g.user:
        return redirect(url_for('auth.login'))
    
    # Get the animal, ensuring it belongs to the current user
    animal = Animal.query.filter_by(id=animal_id, user_id=g.user.id).first_or_404()
    
    return render_template('animals/view.html', animal=animal) 