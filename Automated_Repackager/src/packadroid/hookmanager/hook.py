class Hook:
    def __init__(self, t, location, cls, method, payload_apk_path, payload_dec_path):
        """
            Create a new hook for the currently handled application.
            This object contains all relevant information necessary to place the hook at the user defined location.

            :param t: Type of the hook. Currently we support 'activity' and 'broadcast_receiver'
            :type t: str

            :param location: Location of the hook. This parameter is type-dependent.
                            If the type is 'activity', this parameter contains the activity we want to hook.
                            If the type is 'broadcast_receiver', the parameter contains the broadcast we want to react to.
                                - Possible values:
                                    -> on_power_connected
                                    -> on_power_disconnected
                                    -> on_boot_completed
                                    -> on_receive_sms
                                    -> on_incoming_call
                                    -> on_outgoing_call
            :type location: str

            :param cls: The hook will call the given static method of the class specified with this parameter.
            :type cls: str

            :param method: The method the user wants to call from the given class.
                            The method MUST be declared public and static
            :type method: str

            :param payload_apk_path: Path to the .apk file of the payload.
            :type payload_apk_path: str

            :param payload_dec_path: Path to the decompiled payload we want to inject.
            :type payload_dec_path: str
        """
        self.__type = t
        self.__location = location
        self.__class = cls
        self.__method = method
        self.__payload_apk_path = payload_apk_path
        self.__payload_dec_path = payload_dec_path

    def get_type(self):
        return self.__type

    def get_location(self):
        return self.__location

    def get_class(self):
        return self.__class

    def get_method(self):
        return self.__method

    def get_payload_dec_path(self):
        return self.__payload_dec_path
    
    def get_payload_apk_path(self):
        return self.__payload_apk_path

    def print_hook(self):
        print("Type: " + self.__type)
        print("Location: " + self.__location)
        print("Class: " + self.__class)
        print("Method: " + self.__method)
        print("Payload APK: " + self.__payload_apk_path)
        print("Payload Path: " + self.__payload_dec_path)