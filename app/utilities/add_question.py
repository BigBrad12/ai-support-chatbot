from app.models import Questions
from app import db
from flask import jsonify, redirect, url_for

class AddQuestion:
    def __init__(self, request):
        self.request = request
    
    def add_question(self):
        question = self.request.form.get('question')
        answer = self.request.form.get('answer')
        type = self.request.form.get('type')
        new_question = Questions(
            question=question,
            answer=answer,
            type=type
        )
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('main.send_message_view'))