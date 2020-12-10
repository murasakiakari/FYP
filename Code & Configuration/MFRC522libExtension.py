import Buzzerlib
import MFRC522lib
from SamplePopupGUI import SamplePopupGUI
import time


class SamplePopupGUIExtension(SamplePopupGUI):
    def __init__(self, locker):
        super().__init__()
        if not locker:
            self.LockerLabel.setText(f'You have selected Locker {locker}')
        else:
            self.LockerLabel.setText('')
    
    def cancel_application(self):
        self.close()
        raise UserCancelError


class MFRC522libExtension(MFRC522lib.MFRC522lib):
    DEFAULT_KEY = [0xFF] * 6

    class UserCancelError(BaseException):
        pass

    class UnexpectedError(BaseException):
        pass

    class UnmatchError(BaseException):
        pass

    def __init__(self):
        super().__init__()

    def checksum_generator(self, data):
        return sum([data[i] * -i for i in range(-len(data), 0)]) % 251

    def checksum_auth(self, uid):
        data = self.get_key(uid)
        if self.checksum_generator(data[:4]) != data[4] or self.checksum_generator(data[:5]) != data[5]:
            raise self.AuthenticationError('Not authorised card')

    def get_key(self, uid):
        self.MFRC522_Auth(uid, 1, self.DEFAULT_KEY)
        return self.MFRC522_Read(1)[:6]

    def standard_frame(self, initialize=0, beep=1, gui=0, locker='', *args, **kwargs):
        def standard_frame(function):
            if gui:
                samplepopupgui = SamplePopupGUIExtension(locker)
                samplepopupgui.show()
            else:
                if locker:
                    print(f'You have selected locker {locker}')
                print('Please tap your card')
            buzzer = Buzzerlib.Buzzerlib(beep)
            while 1:
                status = self.MFRC522_Request()
                if status == self.OK:
                    try:
                        uid = self.MFRC522_Anticoll()
                        self.MFRC522_SelectTag(uid)
                        self.checksum_auth(uid)
                        buzzer.notification()
                        start_time = time.time()
                        kwargs['uid'] = uid
                        if not initialize:
                            kwargs['access_key'] = self.get_key(uid)
                        result = function(**kwargs)
                        self.MFRC522_StopCrypto1()
                        print(f'The total elapsed time is {time.time() - start_time:.5f}s')
                        buzzer.finish()
                        break
                    except (self.AuthenticationError, self.CommunicationError, self.IntegrityError):
                        print('Please tap you card again')
                        self.MFRC522_StopCrypto1()
                    except self.UserCancelError:
                        self.MFRC522_StopCrypto1()
                        return
                    except self.UnmatchError:
                        return
            return result
        return standard_frame
