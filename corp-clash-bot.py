
import pyautogui
import time
import win32gui as wgui
import win32process as wproc
import win32api as wapi
import pymem
import time
import math
import json
import re

def main(*argv):
    window_name = 'Corporate Clash [1.5.5]'# Launcher'#'Toontown Rewritten'
    handle = wgui.FindWindow(None, window_name)
    print("Window `{0:s}` handle: 0x{1:016X}".format(window_name, handle))
    if not handle:
        print("Invalid window handle")
        return

    remote_thread, _ = wproc.GetWindowThreadProcessId(handle)
    wproc.AttachThreadInput(wapi.GetCurrentThreadId(), remote_thread, True)
    pyautogui.press("alt")

    wgui.SetForegroundWindow(handle)
    wgui.SetFocus(handle)
    window_data = wgui.GetWindowRect(handle)
    print(window_data) #find out the actual window size and location of Toontown Rewritten
    
    print(f'Screen Size: {pyautogui.size()}')
    print(f'Initial Cursor Position: {pyautogui.position()}')
    #print(f'Initial Relative Cursor Position: {getRelativeCursorPos(pyautogui.size(), pyautogui.position())}')
    print(f'Final Cursor Position: {pyautogui.position()}')

    pm = pymem.Pymem('CorporateClash.exe')

    # Note: Your first address should look like "13A71F18", almost certainly 8 characters long, starting with "13"

    # Find setactivity_base_address by searching CheatEngine or similar tool for the String of {"cmd":
    # setactivity_base_address = get_address(pm.base_address, [0x13A71F18, 0x20, 0x1D8, 0x38, 0x50], pm)

    # Find coords_base_address by selecting a Toon on the top-left portrait, teleporting "Home", then looking for a Float of "-53.77880096"
    coords_base_address = get_address(pm.base_address, [0x13DF79D8, 0x530, 0x1C0, 0x18, 0x1F0, 0x18, 0x18, 0x40],  pm) # NOTE: offsets for this val appear to be constant!
    hp_base_address =     get_address(pm.base_address, [0x13A40708, 0x158, 0x190, 0x58, 0x38,  0x0,  0x38, 0xB48], pm)

    #jellybeans_base_address = get_address(pm.base_address, [0x13DECCC8, 0x8C8, 0xD8, 0x50, 0x8, 0x8, 0x30], pm)

    # To find a value, we need a static address, plus offsets
    # print(f'Hp Base Address: {hex(hp_base_address)}')
    # print(f'Coords Base Address: {hex(coords_base_address)}')
        
    player = Player(mem_manager=pm,
                    #setactivity_base_address=setactivity_base_address,
                    coords_base_address=coords_base_address,
                    hp_base_address= hp_base_address,
                    )
    
    while 1 == 1:
        print(player.get_all_as_json())
        #move_negative_z(player, 10)
        #turn_north(player)
        time.sleep(1)


class Player():
    def __init__(self, mem_manager, coords_base_address, hp_base_address):
        self.mem_manager = mem_manager
        self.coords_base_address = coords_base_address # several values are stored in this proximity! Might be the player class!
        self.hp_base_address = hp_base_address
        self.map_location = ''
        self.hp_remaining = 0
        self.hp_max = 0
        self.name = ''
        self.x = 0
        self.z = 0
        self.y = 0
        self.direction_degrees = 0
        self.inactive = None

    def get_jellybeans(self):
        """Attempt to get jellybeans value -- this value might not be loaded immediately on game start"""
        try:
            jellybeans_raw = self.mem_manager.read_int(self.jellybeans_base_address + self.jellybeans_offset)
            return jellybeans_raw
        except Exception as ex:
            print("Error: Jellybeans value might not be loaded into memory yet...!")
            return 0

    # tells us if player is idle, and also used to determine addresses for x,y,z and direction
    def get_first_json_from_bytearray(self, array_of_bytes):
        """Attempt to parse a bytearray and return valid ASCII JSON if it exists"""
        open_curlybrace_count = 0
        close_curlybrace_count = 0
        json_end_candidates = []
        for index, byte in enumerate(array_of_bytes):
            if byte == 123: # ASCII value of {
                open_curlybrace_count +=1
            if byte == 125: # ASCII value of }
                close_curlybrace_count +=1
                if open_curlybrace_count == close_curlybrace_count:
                    #print('We may have found a valid complete json!')
                    json_end_candidates.append(index)
        
        #print(f'JSON may have ended at these indexes: {json_end_candidates}')
        
        index_end_of_json = json_end_candidates[0] + 1

        if json_end_candidates:
            return array_of_bytes[0:index_end_of_json]
        else:
            print("Error: No ASCII JSON found in this bytestring!")
            return False


    def get_setactivity_json(self):
        """Fetch values from the variable-length SET_ACTIVITY command JSON string"""

        # Find this value by searching CheatEngine or similar tool for {"cmd":, then getting a pointer to the beginning
        # of the JSON. The JSON will look like below:
        '''
            {
            "cmd": "SET_ACTIVITY",
            "data": {
                "assets": {
                    "large_image": "1137059790284148877"
                },
                "timestamps": {
                    "start": 1699720731000
                },
                "details": "Mr. Hackerbuddy (12/15)",
                "state": "Toontown Central",
                "name": "Toontown: Corporate Clash",
                "application_id": "532686383211479042",
                "type": 0
            },
            "evt": null,
            "nonce": "eb094ff9-b1a0-4bb1-8cca-a0f6dbdeb566"
        }

        This JSON string is variable length, but occupies a constant location in memory
        '''

        setactivity_json_bytearray = self.mem_manager.read_bytes(self.setactivity_base_address + self.setactivity_offset, 600)
        setactivity_json_bytearray_parsed = self.get_first_json_from_bytearray(setactivity_json_bytearray)

        #setactivity_json_bytearray = self.mem_manager.read_bytes(self.setactivity_base_address + self.setactivity_offset, index_end_of_json)
   
        setactivity_json = json.loads(setactivity_json_bytearray_parsed.decode('ascii'))

        return setactivity_json

    def get_x(self):
        """Get the X coordinate float"""
        # X is the first value we read, used to determine other toon vals
        x = self.mem_manager.read_float(self.coords_base_address)
        return x
    
    def get_z(self):
        z = self.mem_manager.read_float(self.coords_base_address + 4)
        return z

    def get_y(self):
        y = self.mem_manager.read_float(self.coords_base_address + 8)
        return y
      
    def get_direction_degrees(self):
        direction = self.mem_manager.read_float(self.coords_base_address + 12)
        direction_degrees = direction % 360 # gives us a value between 0 and 360 degrees
        return direction_degrees
    
    def get_idle_bool(self):
        inactive_bool = self.mem_manager.read_bytes(self.coords_base_address + 24, 1) #bytearray like b'\x01'}
        return inactive_bool[0] == 1 # reading the first value of a bytearray of length of 1

    def get_hp(self):
        hp_start_val = 3872675312 # when toon has -1 health (dead). This value appears to be similar across updates.
        raw_hp = self.mem_manager.read_bytes(self.hp_base_address, 4) # this reads in bytes in the wrong/reversed order...
        reversed_bytes_hp = int(bytes(bytearray(raw_hp)[::-1]).hex(),16) # sorcery! But probably endianness
        return (reversed_bytes_hp - hp_start_val)/32 # each health point is 32. This appears to be true across updates
 
    def load_hp_and_name_and_map_location(self):
        '''Read the SET_ACTIVITY JSON string to get 4 values
           Some of these values are available BEFORE toon selection!
           Others are not loaded until toon is selected
        '''
        setactivity_json = self.get_setactivity_json()
        self.map_location =  setactivity_json['data']['state']
        
        # This value looks like "Dr. Hackerbuddy (12/15)"
        try:
            toon_name_and_hp = self.get_setactivity_json()['data']['details']
            hp_min_max = re.search('\(\d+\/\d+\)',toon_name_and_hp).group() # (12/15)
            self.name = toon_name_and_hp.replace(hp_min_max, '').rstrip()
            hp_min_max_int_arr = hp_min_max.replace('(','').replace(')','').split('/') # [12, 15]
            self.hp_remaining = hp_min_max_int_arr[0] # 12 (current health)
            self.hp_max = hp_min_max_int_arr[1] # 15 (max health)
        except Exception as ex:
            print(ex)
            print("Warning: This data could not be loaded yet!")

         # (12/15)
    
    def get_all_as_json(self):
        #self.load_hp_and_name_and_map_location()
        # toon_json = {'hp_remaining': self.hp_remaining, 
        #              'hp_max': self.hp_max,
        #toon_json = {'jellybeans': self.get_jellybeans(),
                    #  'map_location': self.map_location, 
                    #  'name': self.name,
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
    final_offset = 0x0

    for index, offset in enumerate(offsets):
        if (index + 1) == len(offsets):
            print('Don\'t want to read a pointer for our final value in the chain, simply return an address')
            final_offset = offset
        else:
            # Get the next pointer in the chain
            next_prt_addr = bytestr_to_addr(pm.read_bytes(next_prt_addr + offset, 6).hex())

    return next_prt_addr + final_offset

if __name__ == "__main__":
    main()