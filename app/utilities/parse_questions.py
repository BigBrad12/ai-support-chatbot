from messages_file import q_a
import re
from app.models import Questions, SystemStartMessages
from app import db

class Prompt:
    def __init__(self, q_a):
        self.q_a = q_a

    def update_question_table(self):
       qa_pairs = re.split(r'(Q:|A:)', self.q_a)
       i = 0
       while i < len(qa_pairs):
            if qa_pairs[i] == 'Q:':
               question = qa_pairs[i+1].strip()
               i += 2
               if i < len(qa_pairs) and qa_pairs[i] == 'A:':
                    answer = qa_pairs[i+1].strip()
                    self.store_question(question, answer)
                    i += 2
            elif qa_pairs[i] == 'A:':
                answer = qa_pairs[i+1].strip()
                i += 2
            else:
                i += 1

    def store_question(self, question, answer):
        new_question = Questions(
            question=question,
            answer=answer,
            type=''
        )
        db.session.add(new_question)
        db.session.commit()
    
    def update_system_message_table(self):
        message = q_a
        new_message = SystemStartMessages(
            message=message
        )
        db.session.add(new_message)
        db.session.commit()