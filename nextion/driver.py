from .uart import UART
from .pages import Page
import machine # pylint: disable=import-error

class Driver(object):
    RED    = 63488
    BLUE   =    31
    GRAY   = 33840
    BLACK  =     0
    WHITE  = 65535
    GREEN  =  2016
    BROWN  = 48192
    YELLOW = 65504

    def __init__(self, timeout=None, tx=17, rx=16, baudrate=9600, timer=None):
        read_timeout = timeout if timeout is not None else 100
        self.uart = UART(1,baudrate,tx=tx,rx=rx, timeout=read_timeout)
        self.uart.flush()
        if timer:
            self.uart.set_background_listener(timer, self.display_event)
        self.registered_events = {}
        self.pages = []

    def loadPage(self, spec):
        page = Page.new_page_by_specification(self, spec)
        pages_name = list(map(lambda x: x.name, self.pages))
        if page.name in pages_name:
            print(r"Overriding previous definition for page {page.name}")
            self.pages[pages_name.index(page.name)] = page
        else:
            self.pages.append(page)

    def loadPages(self, specs):
        for spec in specs:
            self.loadPage(spec)

    def register_listener(self, path, callback):
        (page_id, component_id) = self.getPageAndComponentIdByPath(path)
        if page_id not in self.registered_events.keys():
            self.registered_events[page_id] = {}
        self.registered_events[page_id][component_id] = callback

    def unregister_listener(self, path):
        (page_id, component_id) = self.getPageAndComponentIdByPath(path)
        del self.registered_events[page_id][component_id]

    def display_event(self,event):
        if event[0] != b'\x65':
            return
        page_id = ord(event[1])
        component_id = ord(event[2])
        if page_id in self.registered_events.keys():
            if component_id in self.registered_events[page_id]:
                self.registered_events[page_id][component_id](ord(event[3]))

    def getPageAndComponentIdByPath(self, fullpath):
        [page, component] = fullpath.split('.')
        for p in self.pages:
            if p.name == page:
                page_id = p.number
                for c in p.components:
                    if c.name == component:
                        component_id = c.comp_id
                        return page_id, component_id
        return None, None

    def getComponentByPath(self, fullpath):
        [page, component] = fullpath.split('.')
        for p in self.pages:
            if p.name == page:
                for c in p.components:
                    if c.name == component:
                        return c

    def setResponseLevel(self, value):
        self.uart.set('bkcmd', value)

    def setBrightness(self, value, save=False):
        self.uart.set('dim' + 's' if save else '', value)

    def setPage(self, value):
        self.uart.write('page ' + str(value))
    def getPage(self):
        self.uart.flush()
        ret = self.uart.write('sendme', read_feedback=True, check_return=False)
        if ret[0] == b'\x66':
            return 0 if ret[1] == 0xff else ord(ret[1])
        raise ValueError(self.uart.get_nx_error_message(ret[0]))

    def refresh(self, comp_id="0"):
        self.uart.write('ref %s' % comp_id)

    def setText(self, obj, value):
        txt = "b[{}].txt=\"{}\"" if isinstance(obj, int) else '{}.txt="{}"'
        return self.uart.write(txt.format(obj, value))
    
    def getText(self, obj):
        txt = 'get b[{}].txt' if isinstance(obj, int) else 'get {}.txt'
        txt = self.uart.write(txt.format(obj), read_feedback=True, check_return=False)
        if txt[0] == b'\x70':
            return (b"".join(txt[1:])).decode('utf-8', "ignore")

    def setValue(self, obj, value):
        msg = "b[{}].val={}" if isinstance(obj, int) else '{}.val={}'
        return self.uart.write(msg.format(obj, int(value)))
    
    def getValue(self, obj):
        msg = 'get b[{}].val' if isinstance(obj, int) else 'get {}.val'
        msg = self.uart.write(msg.format(obj), read_feedback=True, check_return=False)
        if msg[0] == b'\x71':
            return ord(msg[1]) + 256*ord(msg[2]) + 65536*ord(msg[3]) + 16777216*ord(msg[4])

    def clear(self, color):
        self.uart.write('cls %s' % color)

    def drawPicture(self, x, y, pic, w=None, h=None):
        if w is None or h is None:
            self.uart.write('pic %s,%s,%s' % (x, y, pic))
        else:
            self.uart.write('picq %s,%s,%s,%s,%s' % (x, y, w, h, pic))
    def drawString(self, x1, y1, x2, y2, fontid, fontcolor, backcolor, xcenter,
                   ycenter, sta, string):
        self.uart.write('xstr %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' %
                         (x1, y1, x2 - x1, y2 - y1, fontid, fontcolor,
                          backcolor, xcenter, ycenter, sta, string))
    def drawLine(self, x1, y1, x2, y2, color):
        self.uart.write('line %s,%s,%s,%s,%s' % (x1, y1, x2, y2, color))
    def drawRectangle(self, x1, y1, x2, y2, color):
        self.uart.write('draw %s,%s,%s,%s,%s' % (x1, y1, x2, y2, color))
    def drawBox(self, x1, y1, x2, y2, color):
        self.uart.write('fill %s,%s,%s,%s,%s' % (x1, y1, x2 - x1, y2 - y1, color))
    def drawCircle(self, x, y, r, color):
        self.uart.write('cir %s,%s,%s,%s' % (x, y, r, color))

    def show_page_by_name(self, name):
        result = None
        for page in self.pages:
            if page.name == name:
                result = page
                break
        return result

    def page_reference(self, page_id):
        if len(self.pages) > page_id:
            return self.pages[page_id]

        page = Page(self, page_id)
        self.pages.append(page)
        return page