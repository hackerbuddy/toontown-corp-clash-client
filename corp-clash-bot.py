import pyautogui
import subprocess
import time
import win32gui as wgui
import win32process as wproc
import win32api as wapi
import pymem
import time
import math
import psutil



class Player():
    def __init__(self, mem_manager, hp_base_address, coords_base_address):
        self.mem_manager = mem_manager
        self.hp_base_address = hp_base_address
        self.coords_base_address = coords_base_address
        self.inactive_offset = 0x58 # used for determining idleness, x,y,x and direction
        self.hp_offset = 0x4C8
        self.hp = 0
        self.x = 0
        self.z = 0
        self.y = 0
        self.direction_degrees = 0
        self.inactive = None

    # tells us if player is idle, and also used to determine addresses for x,y,z and direction
    def get_idle_bool(self):
        inactive_bool = self.mem_manager.read_short(self.coords_base_address + self.inactive_offset)
        return inactive_bool == 1

    def get_x(self):
        x_offset = self.inactive_offset - 24
        x = self.mem_manager.read_float(self.coords_base_address + x_offset)
        return x
    
    def get_z(self):
        z_offset = self.inactive_offset - 20
        z = self.mem_manager.read_float(self.coords_base_address + z_offset)
        return z

    def get_y(self):
        y_offset = self.inactive_offset - 16
        y = self.mem_manager.read_float(self.coords_base_address + y_offset)
        return y
      
    def get_direction_degrees(self):
        self.direction_offset = self.inactive_offset - 12
        direction = self.mem_manager.read_float(self.coords_base_address + self.direction_offset)
        direction_degrees = direction % 360 # gives us a value between 0 and 360 degrees
        return direction_degrees

    def get_hp(self):
        hp_start_val = 872609264 #16208 # hp starts with a weird value
        toon_hp_raw = self.mem_manager.read_long(self.hp_base_address + self.hp_offset) #2 bytes
        toon_hp = (toon_hp_raw - hp_start_val)/32
        return toon_hp
    
    def get_all_as_json(self):
        toon_json = {'hp': self.get_hp(),
                     'x': round(self.get_x(), 2), 
                     'z': round(self.get_z(), 2),
                     'y': round(self.get_y(), 2),
                     'direction_degrees': round(self.get_direction_degrees(), 2),
                     'inactive': self.get_idle_bool()}
        return toon_json

    
    def check_if_memory_deallocated(self):
        if self.x == 0.0 and self.x == self.z == self.y == self.direction_degrees:
            raise Exception("Critical Memory Error: MEMORY HAS BEEN DEALOCATED. PLEASE RELOAD SCENE!")


def get_coords_helper():
    # launch game manually, then move your mouse around!
    while 1 == 1:
        print(f'Final Cursor Position: {pyautogui.position()}')


def start_launcher_play_game(select_account_x, select_account_y):
    try:
        # See if Launcher is already up and running
        handle = switch_to_window('Corporate Clash Launcher')
    except:
        # Launch launcher if not up and running
        subprocess.run(["cmd.exe", "/c", "start", "/d", "C:/Program Files/Corporate Clash", "new_launcher.exe"], timeout=15)
        time.sleep(6)
        handle = switch_to_window('Corporate Clash Launcher')

    switch_to_window('Corporate Clash Launcher')
    time.sleep(5)

    # click on account selector
    pyautogui.moveTo(select_account_x, select_account_y, 1)
    pyautogui.leftClick()

    # select account
    pyautogui.moveTo(select_account_x, select_account_y + 60, 1)
    pyautogui.leftClick()

    # hit the big PLAY button
    pyautogui.moveTo(select_account_x + 140, select_account_y + 200, 1)
    pyautogui.leftClick()

def kill_game(process_name = "CorporateClash.exe"):
    for proc in psutil.process_iter():
    # check whether the process name matches
        if proc.name() == process_name:
            proc.kill()

def start_game():
    select_account_x = 1212
    select_account_y = 302

    current_game_window_handle = 'Corporate Clash [1.5.2]'
    start_launcher_play_game(select_account_x, select_account_y)

    # Wait for actual game to start...
    time.sleep(15)

    game_loaded = False
    attempts = 0
    while not game_loaded and attempts < 30:
        try:
            handle = switch_to_window(current_game_window_handle)
        except:
            print('Game not loaded yet...ugh')
            attempts+=1
            time.sleep(1)
        
        game_loaded = True

    if not game_loaded:
        raise Exception("Error: The game never loaded!!")
    
    # Wait some more...just because game has started, doesn't mean our game menu is ready...!
    time.sleep(5)

    pyautogui.leftClick()

    # Small delay to load our characters
    time.sleep(4)

    # Selecting character on top left
    pyautogui.moveTo(596, 463, 1)
    pyautogui.leftClick()

    # "Play this Toon" menu, click it
    pyautogui.moveTo(771, 776, 1)
    pyautogui.leftClick()

def main(*argv):
    
    start_game()
    exit()

    pm = pymem.Pymem('CorporateClash.exe')

    hp_base_address = get_address(pm.base_address, [0x13A73F60, 0x60, 0x30, 0xE0, 0x38, 0x270, 0x68], pm)
    coords_base_address = get_address(pm.base_address, [0x13DED878, 0x1D0, 0x20, 0x38, 0x1A8, 0xB8], pm)
    
    # To find a value, we need a static address, plus offsets
    # print(f'Hp Base Address: {hex(hp_base_address)}')
    # print(f'Coords Base Address: {hex(coords_base_address)}')
        
    player = Player(mem_manager=pm,
                    hp_base_address=hp_base_address,
                    coords_base_address=coords_base_address,
                    )
    
    while 1 == 1:
        print(player.get_all_as_json())
        #move_negative_z(player, 10)
        #turn_north(player)
        time.sleep(1)


def move_positive_x(player, distance, timeout_seconds=10, precision=1):
    turn_east(player)
    current_x = player.get_x()
    goal_x = current_x + distance
    distance_from_goal = abs(goal_x - current_x)
    #print(f'Current x is ${current_x}. We want to move {distance} units, to {goal_x}')
    #move_speed = .1 # as we get closer, make smaller movements
    closest_distance = distance

    # Start a timer for our timeout function. If timeout is exceeded, we stop moving.
    start_time = time.perf_counter()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    while round(current_x, precision) != round(goal_x, precision) and elapsed_time < timeout_seconds:
        current_x = player.get_x() # update the current value

        distance_from_goal = abs(goal_x - current_x)
        if distance_from_goal < closest_distance:
            closest_distance = distance_from_goal

        if current_x < goal_x: # we're not there yet
            with pyautogui.hold('up'):
                pyautogui.sleep(.005 * distance_from_goal)
        if current_x > goal_x: # we overshot our goal!
            with pyautogui.hold('down'):
                pyautogui.sleep(.005 * distance_from_goal)

        #print(f'current x {current_x}, distance from goal: {distance_from_goal}, closest_distance: {closest_distance}')
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

def move_negative_x(player, distance, timeout_seconds=10, precision=1):
    turn_west(player)
    current_x = player.get_x()
    goal_x = current_x - distance
    distance_from_goal = abs(goal_x - current_x)
    #print(f'Current x is ${current_x}. We want to move {distance} units, to {goal_x}')
    #move_speed = .1 # as we get closer, make smaller movements
    closest_distance = distance

    # Start a timer for our timeout function. If timeout is exceeded, we stop moving.
    start_time = time.perf_counter()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    while round(current_x, precision) != round(goal_x, precision) and elapsed_time < timeout_seconds:
        current_x = player.get_x() # update the current value

        distance_from_goal = abs(goal_x - current_x)
        if distance_from_goal < closest_distance:
            closest_distance = distance_from_goal

        if current_x > goal_x: # we're not there yet
            with pyautogui.hold('up'):
                pyautogui.sleep(.005 * distance_from_goal)
        if current_x < goal_x: # we overshot our goal!
            with pyautogui.hold('down'):
                pyautogui.sleep(.005 * distance_from_goal)

        #print(f'current x {current_x}, distance from goal: {distance_from_goal}, closest_distance: {closest_distance}')
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

def move_positive_z(player, distance, timeout_seconds=10, precision=1):
    turn_north(player)
    current_z = player.get_z()
    goal_z = current_z + distance
    distance_from_goal = abs(goal_z - current_z)
    #print(f'Current z is ${current_z}. We want to move {distance} units, to {goal_z}')
    #move_speed = .1 # as we get closer, make smaller movements
    closest_distance = distance

    # Start a timer for our timeout function. If timeout is exceeded, we stop moving.
    start_time = time.perf_counter()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    while round(current_z, precision) != round(goal_z, precision) and elapsed_time < timeout_seconds:
        current_z = player.get_z() # update the current value

        distance_from_goal = abs(goal_z - current_z)
        if distance_from_goal < closest_distance:
            closest_distance = distance_from_goal

        if current_z < goal_z: # we're not there yet
            with pyautogui.hold('up'):
                pyautogui.sleep(.005 * distance_from_goal)
        if current_z > goal_z: # we overshot our goal!
            with pyautogui.hold('down'):
                pyautogui.sleep(.005 * distance_from_goal)

        #print(f'current z {current_z}, distance from goal: {distance_from_goal}, closest_distance: {closest_distance}')
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

def move_negative_z(player, distance, timeout_seconds=10, precision=1):
    turn_south(player)
    current_z = player.get_z()
    goal_z = current_z - distance
    distance_from_goal = abs(goal_z - current_z)
    #print(f'Current z is ${current_z}. We want to move {distance} units, to {goal_z}')
    #move_speed = .1 # as we get closer, make smaller movements
    closest_distance = distance

    # Start a timer for our timeout function. If timeout is exceeded, we stop moving.
    start_time = time.perf_counter()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    while round(current_z, precision) != round(goal_z, precision) and elapsed_time < timeout_seconds:
        current_z = player.get_z() # update the current value

        distance_from_goal = abs(goal_z - current_z)
        if distance_from_goal < closest_distance:
            closest_distance = distance_from_goal

        if current_z > goal_z: # we're not there yet
            with pyautogui.hold('up'):
                pyautogui.sleep(.005 * distance_from_goal)
        if current_z < goal_z: # we overshot our goal!
            with pyautogui.hold('down'):
                pyautogui.sleep(.005 * distance_from_goal)

        #print(f'current z {current_z}, distance from goal: {distance_from_goal}, closest_distance: {closest_distance}')
            # End timer
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        #print("Time spent moving: ", elapsed_time)


def turn_to_degrees(degrees_goal, player):
    print(f'degrees before turning: {player.get_direction_degrees()}')
    degrees_to_turn = degrees_goal - player.get_direction_degrees()

    alternate_degrees_to_turn = degrees_to_turn
    alternate_degrees_to_turn = correct_degrees(alternate_degrees_to_turn)

    print(f'degrees_to_turn:{degrees_to_turn} or {alternate_degrees_to_turn}')
    
    
    # when choosing to turn a direction, you will ALWAYS have two options:
    # 1. Turn left
    # 2. Turn right
    #
    # However, turning one way will usually be faster than turning the other way.
    #
    # Thus, we want to find out which way is "closer" in degrees, and turn THAT way
    #
    # This is made slightly complicated since 0 degrees equals 360 degrees
    # We can adjust for this by always subtracting/adding 360 degrees



    # We have two paths: degrees_to_turn OR alternate_degrees_to_turn
    # Which one is closer? Which one is closer to ZERO DEGREES AWAY?
 
    if abs(degrees_to_turn) < abs(alternate_degrees_to_turn):
        #print(f'Primary {degrees_to_turn} is closer, turning this way!')
        turn(degrees_to_turn, player)
    elif abs(alternate_degrees_to_turn) <= abs(degrees_to_turn):
        #print(f'Alt {alternate_degrees_to_turn} is closer, turning this way!')
        turn(alternate_degrees_to_turn, player)

    print(f'final degrees after turning: {player.get_direction_degrees()}')


def turn(degrees_to_turn, player):
    # doing this more than once will increase accuracy
    # start_degrees = player.get_direction_degrees()
    # start_degrees = correct_degrees(start_degrees)
    
    # Make an initial turn, this will get us "pretty close"
    if degrees_to_turn > 0:
        #print(f'{degrees_to_turn} is > 0, so turning left!')
        with pyautogui.hold('left'): # will increase degrees
            pyautogui.sleep(abs(degrees_to_turn)/100) #.01 seconds == 1 degree
    if degrees_to_turn < 0:
        #print(f'{degrees_to_turn} is > 0, so turning right!')
        with pyautogui.hold('right'): # will decrease degrees
            pyautogui.sleep(abs(degrees_to_turn)/100) #.01 seconds == 1 degree

    # Now try to get as close as goal as possible
    # current_degrees = player.get_direction_degrees()
    # current_degrees = correct_degrees(current_degrees)
    # distance_from_goal = abs(current_degrees - start_degrees)
    # print(f'distance_from_goal:{distance_from_goal}')
    #degrees_to_turn = degrees_to_turn - player.get_direction_degrees()

# trigonometry sorcery!
def correct_degrees(degrees):
    if degrees > 0:
        degrees -= 360
    elif degrees < 0:
        degrees += 360
    return degrees

def turn_north(player):
    print("Turning north!")
    turn_to_degrees(0, player)

def turn_south(player):
    print("Turning south!")
    turn_to_degrees(180, player)

def turn_east(player):
    print("Turning east!")
    turn_to_degrees(270, player)

def turn_west(player):
    print("Turning west!")
    turn_to_degrees(90, player)



def fish_bot(cast_button_x, cast_button_y, max_fish_in_bucket, time_to_wait_for_fish_to_bite):
    casts = 0
    # max_fish_in_bucket = 1
    # time_to_wait_for_fish_to_bite = 2
        # pyautogui.moveTo(957, 757, 1) # CAST button coords
        # pyautogui.dragTo(1000, 905, button='left', duration=1)
    while(casts < max_fish_in_bucket):
        pyautogui.moveTo(cast_button_x, cast_button_y, 1) # CAST button coords
        pyautogui.dragTo(cast_button_x + 43, cast_button_y + 150, button='left', duration=1)
        time.sleep(time_to_wait_for_fish_to_bite)
        casts +=1
        if casts == max_fish_in_bucket: # then go sell fish!
            casts = 0
            pyautogui.press("escape")
            time.sleep(1.5)
            # # go to sell fish
            with pyautogui.hold("left"):
                pyautogui.sleep(1.8) #makes a perfect 180 turn
            with pyautogui.hold("up"):
                pyautogui.sleep(0.25)
            with pyautogui.hold("right"):
                pyautogui.sleep(0.9)
            with pyautogui.hold("up"):
                pyautogui.sleep(1.35)
            pyautogui.moveTo(1257, 814, 1) #Move to the SELL ALL button
            pyautogui.leftClick() # Click the "Sell All" button
            time.sleep(.2)
            with pyautogui.hold("left"):
                pyautogui.sleep(1.8) #makes a perfect 180 turn
            with pyautogui.hold("up"):
                pyautogui.sleep(1.3)
            with pyautogui.hold("left"):
                pyautogui.sleep(.9) #makes a perfect 180 turn
            with pyautogui.hold("up"):
                pyautogui.sleep(0.25)
            time.sleep(2.5)

def bytestr_to_addr(my_byte_string):
    i = 0
    new_str = ''
    for count, char in enumerate(my_byte_string):
        new_str += char
        if count != 0 and count%2 != 0:
            new_str+= ' '

    bytes_array = new_str.split() #little endian..?
    bytes_array.reverse()
    
    address_str = ''
    for byte in bytes_array:
        address_str += byte

    
    address_str = address_str[1:] #remove leading number
    
    address_str = '0x' + address_str
    
    hex_int = int(address_str, base=16)
    #new_int = hex_int + 0x200 #https://stackoverflow.com/questions/21879454/how-to-convert-a-hex-string-to-hex-number
    return hex_int

def get_address(start_address, offsets, pm):
    next_prt_addr = start_address
    for offset in offsets:
        next_prt_addr = bytestr_to_addr(pm.read_bytes(next_prt_addr + offset, 6).hex())

    return next_prt_addr

def switch_to_window(window_name):
    handle = wgui.FindWindow(None, window_name)
    print("Window `{0:s}` handle: 0x{1:016X}".format(window_name, handle))
    if not handle:
        raise Exception(f"Error: {window_name} is an invalid window handle. Are you sure it is running?")
    remote_thread, _ = wproc.GetWindowThreadProcessId(handle)
    wproc.AttachThreadInput(wapi.GetCurrentThreadId(), remote_thread, True)
    pyautogui.press("alt")
    wgui.SetForegroundWindow(handle)
    wgui.SetFocus(handle)
    return handle

if __name__ == "__main__":
    main()