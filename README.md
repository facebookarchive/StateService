# StateService

StateService is a state-machine-as-a-service and solves the problem of
coordinating tasks that must occur in a sequence on one or more
machines.

## Examples

Describe a state machine using YAML.

```yaml
--- states.yaml ---
current_state: green_state
states:
  - name: green_state
    func: increment
    current:
      key: count
      value: 0
    target:
      name: red_state
      when:
        key: count
        value: 1
  - name: red_state
    func: increment
    current:
      key: count
      value: 0
    target:
      name: blue_state
      when:
        key: count
        value: 1
  - name: blue_state
```

Run a local instance of StateService.

```sh
> ./state_service --chart states.yaml &> /dev/null &
```

Use cURL to query and update the state machine defined by `states.yaml`.

```sh
# Confirming initial state (green)...
> curl -sIX GET http://localhost:5000/state?state=green_state | grep 200
# Output is 200 OK
# Transition from green state to new state (red)...
> curl -sIX PUT http://localhost:5000/state?state=green_state
# Confirming new state (red)...
> curl -sIX GET http://localhost:5000/state?state=red_state | grep 200
# Output is 200 OK
# Confirming old state (green) is inactive...
> curl -sIX GET http://localhost:5000/state?state=green_state | grep 406
# Output is 406
# Transitioning from red state to new state (blue)..."
> curl -sIX PUT http://localhost:5000/state?state=red_state
# Confirming new state (blue)...
> curl -sIX GET http://localhost:5000/state?state=blue_state | grep 200
# Output is 200 OK
```

## Requirements

StateService requires:

- Linux or macOS
- Python 3.6+

## Installing StateService

Clone this git repository and use `pip` to install its dependencies.

```sh
# Clone this git repository
> git clone https://github.com/facebookincubator/StateService.git
# Create a virtualenv
> python -m venv state_service
> . state_service/bin/activate
# Use `pip` to install dependencies
> cd StateService
> pip install -r requirements.txt
```

## Building StateService

We recommend using [xar](https://github.com/facebookincubator/xar) to
build StateService. Although StateService's dependencies as wheels are not
available (namely, 'itsdangerous' and 'python-click'), `xar` files will
provide a single binary for deploying StateService.

Check [Python Wheels](https://www.pythonwheels.com) for updates.

## Testing StateService

We use `pytest` and included a `Makefile`, so that you can run

```sh
> make test
```

to test StateService.

## How StateService works

StateService is a Flask application that listens for GET and PUT
requests and responds with HTTP status codes (200, 406, or 500). These
status codes represent a YES/NO response when a machine queries the
current state or wants to update the current state.

## Full documentation

### Describing States

StateService reads a list of states from a YAML file and identifies an
initial state for a machine (or machines). An example of a list of states is:

```yaml
current_state: green_state
states:
  - name: green_state
    func: increment
    current:
      key: count
      value: 0
    target:
      name: red_state
      when:
        key: count
        value: 1
  - name: red_state
    func: increment
    current:
      key: count
      value: 0
    target:
      name: blue_state
      when:
        key: count
        value: 1
  - name: blue_state
```

In this example, the current state is `green_state`. `green_state` is
defined fully with its name, a `func` attribute (`increment`), its
current attributes (a key/value pair that describes a `count` key with a
value of 0), and a target state to which it transitions when
`green_state`'s `count` becomes 1. The `func` key describes a method on
the `State` class (see `state.py`); in the case of `increment`, the
method increments the current state's `key` by 1.

Other states are defined similarly, however, the final state is
described only by its name (more precisely, it's identified by the
absence of a `func` attribute).

### StateService

StateService provides a state-machine-as-a-service. StateService reads a
linear state machine (described using YAML, as above) and records the
current state as one or more machines query and update its state machine.

After each update (PUT request), StateService persists its state, so
failures in the service do not result in inconsistent state (by default,
file storage is used).


StateService uses HTTP to integrate with software automation tools like
Chef to coordinate state across several machines. For example, if one
machine requires its group to be in a certain state before performing an
action, it can query StateService from a Chef resource:

```rb
change_command = './change.sh'
execute 'change_machine' do
  cwd home_dir
  command "#{change_command} && curl -K didChangeMachine.curl"
  only_if 'curl -K canChangeMachine.curl', :cwd => home_dir
end
```

`canChangeMachine.curl` describes a GET request from StateService, e.g.,
`https://state_service/state?state=canChangeMachineState`. If this
request returns 200, the Chef resource will proceed to execute the
command; otherwise, this resource will not execute. After executing the
command, `didChangeMachine.curl` is used to update StateService using a
PUT request, e.g.,
`https://state_service/state?state=canChangeMachineState`.

## Contributing

See the CONTRIBUTING file for how to help out and read our Code of
Conduct (CODE\_OF\_CONDUCT.md).

## License

StateService is MIT licensed, as found in the LICENSE file.
