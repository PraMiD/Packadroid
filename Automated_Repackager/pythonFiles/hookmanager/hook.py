class Hook:
    def __init__(self, t, location, cls, method):
        """
            Create a new hook for the currently handled application.
            This object contains all relevant information necessary to place the hook at the user defined location.

            :param t: Type of the hook. Currently we support 'activity' and 'broadcast_receiver'
            :type t: str

            :param location: Location of the hook. This parameter is type-dependent.
                            If the type is 'activity', this parameter contains the activity we want to hook.
                            If the type is 'broadcast_receiver', the parameter contains the broadcast we want to react to.
            :type location: str

            :param cls: The hook will call the given static method of the class specified with this parameter.
            :type cls: str

            :param method: The method the user wants to call from the given class.
                            The method MUST be declared public and static
            :type method: str
        """
        self.__type = t
        self.__location = location
        self.__class = cls
        self.__method = method

    def get_type(self):
        return self.__type

    def get_location(self):
        return self.__location

    def get_class(self):
        return self.__class

    def get_method(self):
        return self.__method