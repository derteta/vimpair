class TestContext(object):

    def __init__(self, name, **k):
        self.__name__ = name
        self.__named_properties = k

    def __getattr__(self, name):
        return self.__named_properties[name] \
                if name in self.__named_properties \
                else super(TestContext, self)._getattr__(name)
