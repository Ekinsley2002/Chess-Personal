# SubProcess.py

import subprocess
import threading
import queue

class ChessEngine:
    def __init__(self, executable_path):
        # Start the C subprocess
        self.process = subprocess.Popen(
            [executable_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line-buffered for real-time communication
        )

        # Queue to store output lines
        self.output_queue = queue.Queue()

        # Start a thread to read the subprocess output
        self.output_thread = threading.Thread(target=self._read_output)
        self.output_thread.daemon = True
        self.output_thread.start()

        # Send the initial '3' to start the C program
        self.send_initial_input()

    def send_initial_input(self):
        try:
            initial_input = '3\n'
            print(f"Sending initial input to C: {initial_input.strip()}")
            self.process.stdin.write(initial_input)
            self.process.stdin.flush()
        except Exception as e:
            print(f"Error sending initial input: {e}")

    def _read_output(self):
        while True:
            line = self.process.stdout.readline()
            if line == '':
                break  # Subprocess has terminated
            self.output_queue.put(line.strip())

    def _get_output(self, expected_lines=24):
        output_lines = []
        while len(output_lines) < expected_lines:
            try:
                # Increase timeout to 10 seconds to allow more time for the C program
                line = self.output_queue.get(timeout=10)
                if len(line.split()) == 8:  # Only consider lines with 8 space-separated items
                    output_lines.append(line)
                else:
                    # Debugging: Print skipped lines
                    print(f"Skipped non-board line: {line}")
            except queue.Empty:
                print("Timeout while waiting for output from C program.")
                break
        return output_lines

    def get_initial_board(self):
        try:
            output_lines = self._get_output(24)
            if len(output_lines) < 24:
                print("Incomplete initial board data received.")
                return None, None, None

            board_rows = output_lines[:8]
            sides_rows = output_lines[8:16]
            highlights_rows = output_lines[16:24]

            board = [row.split() for row in board_rows]
            sides = [row.split() for row in sides_rows]
            highlights = [row.split() for row in highlights_rows]

            return board, sides, highlights

        except Exception as e:
            print(f"Error getting initial board: {e}")
            return None, None, None

    def select_piece(self, row, col):
        try:
            # **Swap the order: send 'col row' instead of 'row col'**
            selection_input = f'{col} {row}\n'
            print(f"Selecting piece at: {selection_input.strip()}")
            self.process.stdin.write(selection_input)
            self.process.stdin.flush()

            # Expect two sets of outputs: with highlights and without
            first_output = self._get_output(24)
            second_output = self._get_output(24)

            if len(first_output) < 24 or len(second_output) < 24:
                print("Incomplete board data received after selection.")
                return None, None, None

            # Use the first output which has highlights
            board_rows = first_output[:8]
            sides_rows = first_output[8:16]
            highlights_rows = first_output[16:24]

            board = [row.split() for row in board_rows]
            sides = [row.split() for row in sides_rows]
            highlights = [row.split() for row in highlights_rows]

            return board, sides, highlights

        except Exception as e:
            print(f"Error selecting piece: {e}")
            return None, None, None

    def move_piece(self, end_row, end_col):
        try:
            # **Swap the order: send 'col row' instead of 'row col'**
            move_input = f'{end_col} {end_row}\n'
            print(f"Moving piece to ({end_col}, {end_row})")
            self.process.stdin.write(move_input)
            self.process.stdin.flush()

            # Read the updated board from the C subprocess
            output_lines = self._get_output(24)
            if len(output_lines) < 24:
                print("Incomplete board data received after move.")
                return None, None, None

            board_rows = output_lines[:8]
            sides_rows = output_lines[8:16]
            highlights_rows = output_lines[16:24]

            board = [row.split() for row in board_rows]
            sides = [row.split() for row in sides_rows]
            highlights = [row.split() for row in highlights_rows]

            return board, sides, highlights

        except Exception as e:
            print(f"Error moving piece: {e}")
            return None, None, None

    def close(self):
        self.process.terminate()
        self.process.wait()
