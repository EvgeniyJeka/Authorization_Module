

class SqlManager(object):

    def get_users(self)-> set:
        return {"JustMe", "JustYou"}

    def get_all_tokens(self)->set:
        return {"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiSnVzdE1lIiwicGFzc3dvcmQiOiJNeVBh"
                "c3N3b3JkIn0.Rq500BSVurkKXmwjsu-_dskPeS7VezfpF-C0qovipv8"}

    def save_jwt_key_time(self, encoded_jwt, key, token_creation_time):
        return True

    def get_password_by_username(self, username):
        return hash("MyPassword")

    def get_data_by_token(self, token):
        return "tempKey", 1648743766.707471

    def get_allowed_actions_by_token(self, token):
        return [1, 2, 3]

# DB TABLE should contain the following rows: user ID, username, password (hashed),
# JWT generation key, JWT generation time

if __name__ == '__main__':
    a = '22 33 45'
    b = list(a.split(" "))
    print(b)
