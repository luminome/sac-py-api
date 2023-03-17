import os
from project import create_app


app = create_app()

if __name__ == '__main__':

    app.run(debug=True, port=os.getenv("PORT", default=5000))
