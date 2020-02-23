class Component(object):
	def __init__(self, page, comp_id, name):
		self.comp_id = comp_id
		self.name = name
		self.page = page
		self.driver = page.driver

	def refresh(self):
		self.driver.refresh(self.comp_id)

	def getFullpath(self):
		return "{}.{}".format(self.page.name, self.name)

	@staticmethod
	def new_component_by_specification(page, specs):
		type = specs['type']
		comp_id = specs['id']
		name = specs['name']
		value = specs['value'] if 'value' in specs.keys() else None
		if "text"==type:
			return Text(page, comp_id, name, value)
		elif "number"==type:
			return Number(page, comp_id, name, value)
		elif "button"==type:
			return Button(page, comp_id, name, value)
		elif "gauge"==type:
			return Gauge(page, comp_id, name, value)
		elif "hotspot"==type:
			return HotSpot(page, comp_id, name)
		elif "waveform"==type:
			return WaveForm(page, comp_id, name)
		return None

class Text(Component):
	def __init__(self, page, comp_id, name, value=None):
		super().__init__(page, comp_id, name)
		if value:
			self.value = None
			self.set(value)
		else:
			self.get()

	def get(self, fullpath=True):
		self.value = self.driver.getText(self.getFullpath() if fullpath else self.name)
		return self.value

	def set(self, value, fullpath=False):
		if value != self.value:
			self.value = value
			self.driver.setText(self.getFullpath() if fullpath else self.name, value)

class Button(Text):
	pass

class Number(Text):
	def get(self, fullpath=True):
		self.value = self.driver.getValue(self.getFullpath() if fullpath else self.name)
		return self.value

	def set(self, value, fullpath=True):
		self.driver.setValue(self.getFullpath() if fullpath else self.name, value)

class Gauge(Number):
	pass


class HotSpot(Component):
	pass

class WaveForm(Component):
	def add(self, channel, value):
		self.driver.write("add " + self.comp_id + "," + channel + "," + value)


