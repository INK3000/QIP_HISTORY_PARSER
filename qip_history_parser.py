from datetime import datetime
import os

# OWNER_NICK is used to specify the owner of the chat in history
OWNER_NICK = 'Me'


class Message:
    def __init__(self, data):
        self.msg_number = int.from_bytes(data[10: 14], 'big')
        self.timestamp = int.from_bytes(data[18: 22], 'big')
        self.is_sent = True if int.from_bytes(data[26: 27], 'big') else False
        self.msg_size = (int.from_bytes(data[31: 35], 'big'))
        self._text = data[35: 35 + self.msg_size]

    def bytes_to_text(self):
        # Since messages are stored in an encrypted form, it is necessary to decode them
        bytes_ = self._text
        ba = bytearray()
        for i, b in enumerate(bytes_):
            try:
                decoded_b = (255 - b - i - 1)
                while decoded_b < 0:
                    decoded_b = 256 + decoded_b
                ba.append(decoded_b)
            except ValueError as e:
                return 'Error while trying decode text'
        return ba.decode()

    text = property(bytes_to_text)


class History:
    def __init__(self, data):
        self.all_messages = list()
        uin_len = int.from_bytes(data[44:46], byteorder='big')
        nick_len = int.from_bytes(data[46 + uin_len:48 + uin_len], 'big')
        self.msg_quantity = int.from_bytes(data[34:38], 'big')
        self.uin = data[46: 46 + uin_len].decode()
        self.nick = data[48 + uin_len:48 + nick_len + uin_len].decode()
        self._start_messages = [48 + nick_len + uin_len]
        self.get_all_messages(data)


    def get_all_messages(self, data):
        for msg_number in range(1, self.msg_quantity+1):
            start = self._start_messages[-1]
            sign = (int.from_bytes(data[start + 0: start + 2], 'big'))
            if not sign:
                start -= 1
            msg_block_size = int.from_bytes(data[start + 2:start + 6], 'big')
            self.all_messages.append(Message(data[start:start + msg_block_size + 6]))
            self._start_messages.append(start + msg_block_size + 6)

    def get_message(self, msg_number: int) -> Message:
        # allows to get an instance of the Message class
        # by the sequence number of the message
        if msg_number < 1 or msg_number > self.msg_quantity:
            raise ValueError(f'msg_number must be in range 1 to {self.msg_quantity}')
        return self.all_messages[msg_number - 1]


def get_bytes(filename):
    with open(filename, 'rb') as file:
        data = bytearray(file.read())
        return data


def is_qhf_format(data):
    return data[0:3] == b'QHF'


def write_history_to_file(history: History, filename: str):
    with open(filename, 'w') as file:
        header = f'History conversation with {history.nick} ({history.uin})\n' \
                 f'Contains {history.msg_quantity} message(s) \n\n'
        print(header)
        file.write(header)
        try:
            for i in range(1, history.msg_quantity + 1):
                message = history.get_message(i)
                text = message.text
                sender = OWNER_NICK if message.is_sent else history.nick
                time = datetime.utcfromtimestamp(message.timestamp)
                text_to_write = f'-- {sender} ({time}) \n{text}\n\n'
                file.write(text_to_write)
        except Exception as e:
            print(e)
        else:
            print(f'{filename} was successfully written')


def main():
    path_to_read = ''
    while not os.path.exists(path_to_read):
        path_to_read = input('Enter path to the file or Q for quit:')
        if path_to_read in 'Qq':
            print('The program was completed')
            exit()
    data = get_bytes(path_to_read)
    if is_qhf_format(data):
        history = History(data)
        filename_to_write = f'{history.uin} - {datetime.today()}.txt'
        folder_to_write = ''
        path_to_write = os.path.join(folder_to_write, filename_to_write)
        write_history_to_file(history, path_to_write)
    else:
        print('This file is not QHF format or corrupted. '
              'The program has been stopped')


if __name__ == '__main__':
    main()
