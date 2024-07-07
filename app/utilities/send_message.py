from app import db
from flask import jsonify
import openai
from app.models import SessionData
from sqlalchemy.orm.attributes import flag_modified

class SendTestMessage:
    def __init__(self, request, questions, system_message):
        self.request = request
        self.questions = questions
        self.system_message = system_message

    def build_prompt(self):
        system_prompt = []
        prompt = self.system_message.message
        for question in self.questions:
            prompt += f"Q: {question.question} A: {question.answer}"

        system_prompt.append({
                'role': 'system',
                'content': prompt
        })
        return system_prompt

    # append message from user onto the gpt system prompt json
    def process_message(self):
        prompt = self.build_prompt()
        prompt.append({
            'role': 'user',
            'content': self.request.form.get('message')
        })

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages = prompt,
                temperature = 0.6,
                max_tokens = 350,
                top_p = 1,
                frequency_penalty = 0,
                presence_penalty = 0
            )

            choices: dict = response.get('choices')[0]
            message = choices.message.get('content')
            return jsonify(message)


        except Exception as e:
                response_payload = {
                    "botMessage": e,
                    "responseExpected": False
                }
                return response_payload

# handles the hubspot chat webhook
class WebhookHandler:

    def __init__(self, request, questions, system_message):
        self.request = request
        self.questions = questions
        self.system_message = system_message

        if request.is_json:
            self.payload = request.json
            self.conversation_id = self.payload['session']['conversationId']
            self.user_agent = request.headers.get('user-agent', '')
            self.user_chat_input = self.payload['userMessage']['message']
        elif request.form:
            self.payload = request.form
            self.conversation_id = self.payload.get('conversation_id')
            self.user_chat_input = self.payload.get('content')
            self.user_agent = 'dev.hubspot.com'

    def build_prompt(self):
        system_prompt = []
        prompt = self.system_message.message
        for question in self.questions:
            prompt += f"Q: {question.question} A: {question.answer}"

        system_prompt.append({
                'role': 'system',
                'content': prompt
        })
        return system_prompt 

    def process_webhook(self):
        if 'dev.hubspot.com' in self.user_agent:
            try: 
                prompt = self.build_prompt()
                session_data = SessionData.query.filter_by(conversation_id = str(self.conversation_id)).first()

                if session_data is None:
                    session_data = SessionData(
                        conversation_id=self.conversation_id,
                        messages_array=prompt,
                        prompt_type='',
                        convo=''
                    )
                    db.session.add(session_data)
                    db.session.commit()

                # checks if the initial message is "AI Assistant" or the user input is too long
                respond = self.initial_chat_input_check(self.user_chat_input)
                if respond:
                    return respond

            except Exception as e:
                response_payload = {
                    "botMessage": "Something went wrong. We'll fix it. Please try again later.",
                    "responseExpected": False
                }
                print(e)
                return response_payload
        
            self.update_messages(self.user_chat_input, self.conversation_id, 'user')
            self.update_convo(self.user_chat_input, self.conversation_id, 'user')
            bot_message = self.get_api_response(session_data.messages_array, self.conversation_id)

            return self.successful_response(bot_message)
        
            
        else:
            response_payload = {
                    "botMessage": "sorry, that was not a valid request",
                    "responseExpected": False
                }
            return response_payload

    def successful_response(self, bot_message: str):
        response_payload = {
                    "botMessage": bot_message,
                    "responseExpected": True
                }
        return response_payload
    
    def update_messages(self, new_message, conversation_id, role): 
        current_conversation = SessionData.query.filter_by(conversation_id = str(conversation_id)).first()
        current_conversation.messages_array.append({
            'role': role,
            'content': new_message
        })
        flag_modified(current_conversation, 'messages_array')
        db.session.commit()

    def initial_chat_input_check(self, input: str):
        if len(input) >= 749:
            reduce_by = len(input) - 749
            response_payload = {
                    "botMessage": f"Your message was too long, please shorten your message by ${reduce_by} characters.",
                    "responseExpected": True
                }
            return (response_payload)
        if input == 'AI Assistant':
            response_payload = {
                'botMessage': "Initial message sent.",
                'responseExpected': True
            }
            return response_payload

    def build_string(self, content: list):
        result_string = ""
        for content in content:
            if "content" in content:
                result_string += content['content'] + " "
        return result_string

    def get_api_response(self, messages, conversation_id): # returns the bot message from api call

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages = messages,
                temperature = 0.6,
                max_tokens = 750,
                top_p = 1,
                frequency_penalty = 0,
                presence_penalty = 0
            )
            choices: dict = response.get('choices')[0]
            message = self.cleaned_response(choices.message.get('content'))
            self.update_messages(message, conversation_id, 'assistant')
            self.update_convo(message, conversation_id, 'assistant')

            return message 

        except Exception as e:
            print('Open AI API Error: ', e)
            return('Sorry, something went wrong. The server may be down. Please try again later or contact support.')   

    def cleaned_response(self, dirty_string: str):
        final_string = ""
        final_string = dirty_string.replace("</li>\n<li>", "</li><li>").replace("<ul>\n<li>", "<ul><li>").replace("</li\n></ul>", "</li></ul>").replace("</li>\n</ul>", "</li></ul>").replace("\n\n", "<br>").replace("**", "").replace("###", '')
        return final_string

    def update_convo(self, message, conversation_id, role):

        current_conversation = SessionData.query.filter_by(conversation_id = str(conversation_id)).first()
        if current_conversation.convo == '':
            current_conversation.convo = f"{role.capitalize()}: {message}"
        else:
            current_conversation.convo += f"\n\n{role.capitalize()}: {message}"

        db.session.commit()

    # def get_max_tokens(self, prompt_type: str): 
        # if prompt_type == 'general':
        #     max_tokens = 290
        # elif prompt_type == 'qb_integrations':
        #     max_tokens = 290
        # return max_tokens

    # def num_tokens(self, content: list, encoding_name: str) -> int:
        # encoding = tiktoken.get_encoding(encoding_name)
        # string = self.build_string(content)
        # num_tokens = len(encoding.encode(string))
        # return num_tokens

class TestWebhook:
    def __init__(self, request, questions, system_message):
        self.request = request
        self.conversation_id = request.form.get('conversation_id')
        self.message = request.form.get('content')
        self.role = request.form.get('role')
        self.questions = questions
        self.system_message = system_message

    def process_test_webhook(self):
        return self.request.form
        return {'conversation_id': self.conversation_id, 'role': self.role, 'message': self.message }

    def build_prompt(self):
        system_prompt = []
        prompt = self.system_message.message
        for question in self.questions:
            prompt += f"Q: {question.question} A: {question.answer}"

        system_prompt.append({
                'role': 'system',
                'content': prompt
        })
        return system_prompt 