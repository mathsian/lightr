import pika
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = 'Oh really now'

@app.route('/', methods=['GET','POST'])
def index(sprites=None):
    if request.method == 'POST':
        for sprite in session['sprites']:
            sprite["colour"] = request.form['picker_{}'.format(sprite["index"])]
            sprite["dx"] = request.form['dx_{}'.format(sprite["index"])]
            sprite["dy"] = request.form['dy_{}'.format(sprite["index"])]
        channel.basic_publish(exchange='',
            routing_key='hello',
            body=str(session['sprites']))
    try:
        sprites = session['sprites']
    except KeyError as e:
        sprites = [
                {
                    "index": 0,
                    "name": "One",
                    "colour": "#abcdef",
                    "dx": 0.1,
                    "dy": 0.2
                    },
                {
                    "index": 1,
                    "name": "Two",
                    "colour": "#fedcba",
                    "dx": -0.1,
                    "dy": 0.3
                    }
                ]
        session['sprites'] = sprites
    return render_template('index.html', sprites=sprites)

if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='hello')

    app.run(host='0.0.0.0')

    connection.close()
