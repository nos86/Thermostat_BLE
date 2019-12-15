from . import components

class Page(object):
	def __init__(self, driver, name, page_number=0):
		self.components = []
		self.name = name
		self.driver = driver
		self.number = page_number

	@staticmethod
	def new_page_by_specification(driver, specs):
		page = Page(driver, name=specs['name'], page_number=specs['id'])
		if 'components' in specs.keys():
			for component in specs['components']:
				page.components.append(components.Component \
					.new_component_by_specification(page, component))
		return page

	def component_by_name(self, name):
		for component in self.components:
			if name == component.name:
				return component
		return None

	def hook_text(self, comp_id, value=None):
		component = components.Text(self, comp_id, value)
		self.components.append(component)
		return component

	def show(self):
		self.driver.setPage(self.number)