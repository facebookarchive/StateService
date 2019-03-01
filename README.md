# StateService

StateService is a state machine-as-a-service that reports the state of one or more machines, so that machines can decide the next best step to ensure stability. StateService works with configuration management software to provide self-healing and automated recovery capabilities.

## Examples

StateService can serve an explicit and/or implicit state machine.

### Explicit State Machine

StateService can read a state machine defined explicity in YAML.

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

To use, start an instance of StateService.

```sh
> ./state_service --machine states.yaml &> /dev/null &
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

StateService provides two ways to update its state machine. The first is as above: external HTTP requests cause updates. The second uses a state machine that contains states whose transitions are described using time; in this case, StateService updates its state machine automatically (see 'Asynchronous State Machines' below).

### Implicit State Machine

StateService hosts machine-learning models and responds to requests from `POST /state` to predict the state of the machine making the request.

Start an instance of StateService.

```sh
> ./state_service --config /path/to/conf --models /path/to/models &> /dev/null &
```

where the path to configuration files contains the following JSON file

```json
{
    "name": "colors",
    "team": "state_service",
    "model": "colors_v1.pkl",
    "states": [
        "green",
        "red",
        "blue"
    ]
}
```

Use cURL to query the implicit state machine. Given a JSON file, `models.json`,

```json
{
    "name": "colors", // References the configuration file and finds the target model
    "values": [[500, 0]] // Suitable values for the target model's `predict` method
}
```

```sh
> curl -X POST -d @models.json http://localhost:5000/state
green
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

We recommend using [xar](https://github.com/facebookincubator/xar) to build StateService. Although StateService's dependencies as wheels are not available (namely, 'itsdangerous' and 'python-click'), `xar` files will provide a single binary for deploying StateService.

Check [Python Wheels](https://www.pythonwheels.com) for updates.

## Testing StateService

We use `pytest` and included a `Makefile`, so that you can run

```sh
> make test
```

to test StateService.

## How StateService works

StateService is a Flask application that can be configured as an explicit and/or implicit state machine.

StateService, as an explicit state machine, listens for GET and PUT requests and responds with HTTP status codes (200, 406, or 500). These status codes represent a YES/NO response when a machine queries the current state or wants to update the current state.

As an implicit state machine, StateService listens for POST requests and responds with a state value that is determined by a machine-learning model.

## Full documentation

### StateService and Explicit State Machines

StateService reads a list of states from a YAML file and identifies an initial state for a machine (or machines). The state machine can be synchronous or asynchronous.

#### Synchronous State Machines

An example of a synchronous state machine is:

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

In this example, the current state is `green_state`. `green_state` is defined fully with its name, a `func` attribute (`increment`), its current attributes (a key/value pair that describes a `count` key with a value of 0), and a target state to which it transitions when `green_state`'s `count` becomes 1. The `func` key describes a method on the `State` class (see `state.py`).

#### Asynchronous State Machines

To program an asynchronous state machine, describe a state machine as above, but assign the `func` key with a `time` value:

```yaml
...
states:
  - name: green_state
    func: time
    target:
      name: red_state
      when:
        key: clock
        value: '3000-01-01T12:00:00'
...
```

describes `green_state` that will transition to `red_state` after midday on January 1, 3000. A `current` key is not necessary when the `time` function is used (it is implied that the current `clock` value is the current time on the machine that's running StateService).

---

Two `func` methods are defined: `increment` and `time`. In the case of `increment`, the method increments the current state's `key` by 1; `time` provides the state machine with the ability to transition states automatically depending on a specific time.

The final state of a state machine is described only by its name (more precisely, it's identified by the absence of a `func` attribute).

#### Integrating StateService with Configuration Management Software

StateService provides a state-machine-as-a-service. StateService reads a linear state machine (described using YAML, as above) and records the current state as one or more machines query and update its state machine.

After each update, StateService persists its state, so failures in the service do not result in inconsistent state (by default, file storage is used).

StateService uses HTTP to integrate with software automation tools like Chef to coordinate state across several machines. For example, if one machine requires its group to be in a certain state before performing an action, it can query StateService from a Chef resource:

```rb
# Assuming a synchronous state machine
change_command = './change.sh'
execute 'change_machine' do
  cwd home_dir
  command "#{change_command} && curl -K didChangeMachine.curl"
  only_if 'curl -K canChangeMachine.curl', :cwd => home_dir
end
```

`canChangeMachine.curl` describes a GET request from StateService, e.g., `https://state_service/state?state=canChangeMachineState`. If this request returns 200, the Chef resource will proceed to execute the command; otherwise, this resource will not execute. After executing the command, `didChangeMachine.curl` is used to update StateService using a PUT request, e.g., `https://state_service/state?state=canChangeMachineState`.

When the `func` value is `time`, the Chef resource is defined as:

```rb
# Assuming an asynchronous state machine
change_command = './change.sh'
execute 'change_machine' do
  cwd home_dir
  command change_command
  only_if 'curl -K canChangeMachine.curl', :cwd => home_dir
end
```

where `canChangeMachine.curl` describes a GET request to StateService. This is consistent with the intention that, when state transitions are scheduled at a certain time, we only need to request the current state.

### StateService and Implicit State Machines

To use StateService as an implicit state machine, create JSON files that describe the models available to StateService.

```json
{
    "name": "colors",
    "team": "state_service",
    "model": "colors_v1.pkl",
    "states": [
        "green",
        "red",
        "blue"
    ]
}
```

The above JSON file provides a `name` that will be provided in a `POST /state` request to identify the model, a `team` that is used to identify the subdirectory to search for the `model`, a serialized version of a ML model instance, and a list of `states`. The ML model instance must provide a `predict` method of the form:

```py
def predict(self, values):
    ...
```

This method must return a single-element `list` containing an integer that references one of the states in the JSON file above.

## Contributing

See the CONTRIBUTING file for how to help out and read our Code of Conduct (CODE\_OF\_CONDUCT.md).

## License

StateService is MIT licensed, as found in the LICENSE file.
