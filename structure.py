"""
Relay Controller Abstraction Class
"""
import lib8relind as relay


class RelayController:
    """Controller for Sequent Microsystems 8-relay boards"""
    
    def __init__(self, num_hats=1, relays_per_hat=8):
        """
        HAT controller description
        
        Args:
            num_hats: Number of relay boards (1-6)
            relays_per_hat: Number of relays per board (8)
        """
        self.num_hats = num_hats
        self.relays_per_hat = relays_per_hat
    
    def set_relay(self, stack, relay_num, state):
        """
        Set the state of a single relay
        
        Args:
            stack: Stack number (0 to num_hats-1)
            relay_num: Relay number (1-8)
            state: 0 (OFF) or 1 (ON)
        
        Raises:
            ValueError: If invalid parameters
        """
        self._validate_stack(stack)
        self._validate_relay(relay_num)
        if state not in [0, 1]:
            raise ValueError(f'Invalid state {state}. Must be 0 or 1')
        
        relay.set(stack, relay_num, state)
    
    def get_relay(self, stack, relay_num):
        """
        Get the state of a single relay
        
        Args:
            stack: Stack number (0 to num_hats-1)
            relay_num: Relay number (1-8)
        
        Returns:
            0 (OFF) or 1 (ON)
        
        Raises:
            ValueError: If invalid parameters
        """
        self._validate_stack(stack)
        self._validate_relay(relay_num)
        
        return relay.get(stack, relay_num)
    
    def set_all(self, stack, value):
        """
        Set all relays on a stack using a bitmap
        
        Args:
            stack: Stack number (0 to num_hats-1)
            value: 8-bit bitmap (0-255)
                   0 = all off
                   255 = all on
        
        Raises:
            ValueError: If invalid parameters
        """
        self._validate_stack(stack)
        if value < 0 or value > 255:
            raise ValueError(f'Invalid value {value}. Must be 0-255')
        
        relay.set_all(stack, value)
    
    def get_all(self, stack):
        """
        Get the state of all relays on a stack as a list
        
        Args:
            stack: Stack number (0 to num_hats-1)
        
        Returns:
            List of 8 values [0 or 1, 0 or 1, ...]
            Index 0 = Relay 1, Index 7 = Relay 8
        
        Raises:
            ValueError: If invalid parameters
        """
        self._validate_stack(stack)
        
        bitmap = relay.get_all(stack)
        
        # Convert bitmap to list
        states = []
        for relay_num in range(self.relays_per_hat):
            states.append((bitmap >> relay_num) & 1)
        
        return states
    
    def get_all_stacks(self):
        """
        Get the state of all relays across all stacks
        
        Returns:
            Dictionary with stack_0, stack_1, etc. as keys
            Each value is a list of 8 relay states
        """
        all_states = {}
        for stack in range(self.num_hats):
            try:
                all_states[f'stack_{stack}'] = self.get_all(stack)
            except Exception as e:
                all_states[f'stack_{stack}'] = {'error': str(e)}
        
        return all_states
    
    def turn_on_stack(self, stack):
        """
        Turn on all relays on a specific stack
        
        Args:
            stack: Stack number (0 to num_hats-1)
        
        Raises:
            ValueError: If invalid stack
        """
        self._validate_stack(stack)
        relay.set_all(stack, 255)
    
    def turn_off_stack(self, stack):
        """
        Turn off all relays on a specific stack
        
        Args:
            stack: Stack number (0 to num_hats-1)
        
        Raises:
            ValueError: If invalid stack
        """
        self._validate_stack(stack)
        relay.set_all(stack, 0)
    
    def turn_on_all_stacks(self):
        """
        Turn on all relays across ALL stacks
        
        Returns:
            Dictionary with results for each stack
        """
        results = {}
        for stack in range(self.num_hats):
            try:
                relay.set_all(stack, 255)
                results[f'stack_{stack}'] = 'All relays ON'
            except Exception as e:
                results[f'stack_{stack}'] = f'Error: {str(e)}'
        
        return results
    
    def turn_off_all_stacks(self):
        """
        Turn off all relays across ALL stacks
        
        Returns:
            Dictionary with results for each stack
        """
        results = {}
        for stack in range(self.num_hats):
            try:
                relay.set_all(stack, 0)
                results[f'stack_{stack}'] = 'All relays OFF'
            except Exception as e:
                results[f'stack_{stack}'] = f'Error: {str(e)}'
        
        return results
    
    def _validate_stack(self, stack):
        """Validate stack number"""
        if stack < 0 or stack >= self.num_hats:
            raise ValueError(f'Invalid stack {stack}. Must be 0-{self.num_hats-1}')
    
    def _validate_relay(self, relay_num):
        """Validate relay number"""
        if relay_num < 1 or relay_num > self.relays_per_hat:
            raise ValueError(f'Invalid relay {relay_num}. Must be 1-{self.relays_per_hat}')


# Example usage
if __name__ == '__main__':
    # Create controller for 1 board
    controller = RelayController(num_hats=1)
    
    print("Testing relay controller...")
    
    # Turn on relay 1
    print("\n1. Turn ON relay 1 on stack 0")
    controller.set_relay(0, 1, 1)
    state = controller.get_relay(0, 1)
    print(f"   State: {state}")
    
    # Get all states for one stack
    print("\n2. Get all relay states for stack 0")
    states = controller.get_all(0)
    print(f"   States: {states}")
    
    # Get all states for all stacks
    print("\n3. Get all states across all stacks")
    all_states = controller.get_all_stacks()
    print(f"   All states: {all_states}")
    
    # Turn on all relays on stack 0
    print("\n4. Turn ON all relays on stack 0")
    controller.turn_on_stack(0)
    states = controller.get_all(0)
    print(f"   States: {states}")
    
    # Turn off all relays on stack 0
    print("\n5. Turn OFF all relays on stack 0")
    controller.turn_off_stack(0)
    states = controller.get_all(0)
    print(f"   States: {states}")
    
    # Turn on all relays on all stacks
    print("\n6. Turn ON all relays on ALL stacks")
    results = controller.turn_on_all_stacks()
    print(f"   Results: {results}")
    
    # Turn off all relays on all stacks
    print("\n7. Turn OFF all relays on ALL stacks")
    results = controller.turn_off_all_stacks()
    print(f"   Results: {results}")
