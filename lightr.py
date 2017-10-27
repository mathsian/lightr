import unicornhat as uh
from colour import Color
import pickle
import pika
from queue import Queue, Empty
import threading

uh.set_layout(uh.AUTO)
uh.brightness(0.6)

sprites = [
        {"index":0,"name":"one","dx":0.05,"colour":"#abcdef"},
        {"index":1,"name":"two","dx":0.07,"colour":"#fedcba"}]

w, h = uh.get_shape()

# We want to be efficient about calculating distances
# But at a high enough resolution to look smooth
# So precalculate and save as a binary file for future
try:
    # Load up those distances if they exist
    d = pickle.load(open("d.pickle", "rb"))
except (OSError, IOError) as e:
    # Or calculate them
    # 1 d.p. resolution
    wd = [i/10 for i in range((w+1)*10)]
    hd = [j/10 for j in range((h+1)*10)]
    d = {}
    # Could probs use symmetries to speed this up but I only do it once :)
    for X in wd:
        for Y in hd:
            for i in range(w):
                for j in range(h):
                    # Shortest distance on a discrete torus (unrooted)
                    md = min((i-X)%w, (X-i)%w)**2 + min(
                                (j-Y)%h,(Y-j)%h)**2
                    # Scale by (still squared) distance to give a
                    # quadratic drop off 0 < d < 1
                    d[(X, Y, i, j)] = max(255.-64.*md, 0)/255.
    pickle.dump(d, open("d.pickle", "wb"))


class Layer():
    '''Encapsulates a w by h layer of rgb pixels.
    Has its own update and shader code '''
    def __init__(self, c, dx):
        self.x, self. y = 0., 0.
        self.dx = float(dx)
        self.r, self.g, self.b = (round(x*255) for x in Color(c).rgb)
        self.pixels = [[(0,0,0) for _ in range(w)] for _ in range(h)]
    def update(self):
        # Move point
        self.x = (self.x + self.dx)%w
        self.y = (self.y + 0.01)%h
    def shader(self, i, j):
        # Round off for the distance dictionary
        X = round(self.x,1)
        Y = round(self.y,1)
        dd =  d[(X, Y, i, j)]
        return (round(self.r*dd), round(self.g*dd), round(self.b*dd))

class Display(threading.Thread):
    def __init__(self, queue, layers):
        threading.Thread.__init__(self)
        self.layers = layers
        self.queue = queue
    def run(self):
        while True:
            # Cycle through the layers fast enough to dither
            for layer in self.layers:
                layer.update()
                uh.shade_pixels(layer.shader)
                uh.show()
            # Check if there is are new layers on the queue
            try:
                self.layers = self.queue.get(False)
            except Empty:
                pass
class Check(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='hello')

    def run(self):
        while True:
            method, header, body = self.channel.basic_get(queue='hello',no_ack=True)
            if method and method.NAME != 'Basic.GetEmpty':
                try:
                    sprites = eval(body.decode("UTF-8"))
                    print(sprites)
                    layers = [Layer("#{}".format(sprite["colour"]), sprite["dx"]) for sprite in sprites]
                    self.queue.put(layers)
                except TypeError as e:
                    print("Got body {}".format(body))


if __name__ == '__main__':
    layers = [Layer(sprite["colour"], sprite["dx"]) for sprite in sprites]
    q = Queue()
    display_thread = Display(q, layers)
    check_thread  = Check(q)
    display_thread.start()
    check_thread.start()
