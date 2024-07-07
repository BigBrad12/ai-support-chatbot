from flask import request, render_template, Blueprint, redirect, url_for
from flask_paginate import get_page_parameter
from app.utilities.send_message import WebhookHandler, SendTestMessage, TestWebhook
from app.auth import requires_auth
from app.utilities.add_question import AddQuestion
from app.models import Questions, SystemStartMessages
from app import db

main = Blueprint('main', __name__)

@main.route('/webhook', methods=['POST'])
def webhook():
    questions = Questions.query.all()
    system_message = SystemStartMessages.query.first()
    handler = WebhookHandler(request, questions, system_message)
    return handler.process_webhook()

@main.route('/test_webhook', methods=['GET', 'POST'])
@requires_auth
def test_webhook():
    if request.method == 'GET':
        return render_template('test_webhook.html')
    if request.method == 'POST':
        questions = Questions.query.all()
        system_message = SystemStartMessages.query.first()
        handler = WebhookHandler(request, questions, system_message) 
        return handler.process_webhook()

@main.route('/', methods=['GET'])
@requires_auth
def home():
    return render_template('home.html')

@main.route('/add_question', methods=['GET', 'POST'])
@requires_auth
def add_question():
    if request.method == 'POST':
        add_question = AddQuestion(request)
        return add_question.add_question()
    if request.method == 'GET':
        return render_template('add_question.html')

@main.route('/send_message', methods=['POST', 'GET'])
@requires_auth
def send_message_view():
    if request.method == 'POST':
        questions = Questions.query.all()
        system_message = SystemStartMessages.query.first()
        test_message = SendTestMessage(request, questions, system_message)
        response = test_message.process_message() 
        return render_template('send_message.html', response=response.get_json())
    else:
        return render_template('send_message.html')

@main.route('/prompt', methods=['GET', 'POST'])
@requires_auth
def show_prompt():
    if request.method == 'POST':
        if 'update_all' in request.form:
            page = request.args.get('page', 1, type=int)
            sort_by = request.args.get('sort_by', 'id')
            order = request.args.get('order', 'asc')
            per_page = 50
            questions_query = Questions.query
            if sort_by == 'type':
                if order == 'desc':
                    questions_query = questions_query.order_by(Questions.type.desc())
                else:
                    questions_query = questions_query.order_by(Questions.type.asc())
            else:
                questions_query = questions_query.order_by(Questions.id)

            questions = questions_query.offset((page - 1) * per_page).limit(per_page).all()

            for question in questions:
                question_id = question.id
                question.question = request.form[f'question_{question_id}']
                question.answer = request.form[f'answer_{question_id}']
                question.type = request.form[f'type_{question_id}']
            db.session.commit()
        else:
            question_id = request.form['update']
            page = request.args.get('page', 1, type=int)
            sort_by = request.args.get('sort_by', 'id')
            order = request.args.get('order', 'asc')
            question = Questions.query.get(question_id)
            question.question = request.form[f'question_{question_id}']
            question.answer = request.form[f'answer_{question_id}']
            question.type = request.form[f'type_{question_id}']
            db.session.commit()
        return redirect(url_for('main.show_prompt', page=page, sort_by=sort_by, order=order))

    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')
        per_page = 50

        questions = Questions.query
        if sort_by == 'type':
            if order == 'desc':
                questions = questions.order_by(Questions.type.desc())
            else:
                questions = questions.order_by(Questions.type.asc())
        else:
            questions = questions.order_by(Questions.id)

        total = questions.count()
        questions = questions.offset((page - 1) * per_page).limit(per_page).all()
        total_pages = (total + per_page - 1) // per_page

        return render_template('show_prompt.html', questions=questions, page=page, total_pages=total_pages, sort_by=sort_by, order=order)

@main.route('/system_message', methods=['GET', 'POST'])
@requires_auth
def show_system_message():
    if request.method == 'GET':
        message = SystemStartMessages.query.first()
        return render_template('show_system_message.html', system_message=message.message)
    if request.method == 'POST':
        system_message = request.form['system_message']
        system_start_message = SystemStartMessages.query.first()
        if system_start_message:
            system_start_message.message = system_message
            db.session.commit()
        return redirect(url_for('main.show_system_message'))

# @main.route('/create_system_message', methods=['GET'])
# @requires_auth
# def parse_system_message():
#     if request.method == 'GET':
#         parse_class = Prompt(system_message)
#         return parse_class.update_system_message_table()

# @main.route('/add_qb', methods=['GET'])
# @requires_auth
# def parse_questions():
#     if request.method == 'GET':
#         parse_class = Prompt(q_a)
#         return parse_class.update_question_table()