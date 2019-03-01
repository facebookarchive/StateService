## Change Log

### Version 2.0.0

Introduced implicit state machines available from `POST /state`. This
request receives data from machines and queries machine-learning models,
returning a predicted state based on the data received.

### Version 1.1.0

Replaced synchronous `time` function with an asynchronous version that
uses `threaded.Timer` to transition states without the need for an HTTP
PUT request.

The `StateMachine` class is the interface to states. This interface has
three methods: `build`, `is_current_state`, and `update`.  The
`StateService` class queries and updates `State` instances using this
interface.

### Version 1.0.0

Introduced a `time` function that, upon receiving a HTTP PUT request,
will update the state machine if the target time for a state transition
has passed.

### Version 0.9.0

Introducing a state machine-as-a-service that transitions between states
when a condition, defined in the current state's `dict`, for
transitioning is `True`. The condition of a state is changed in response
to HTTP PUT requests, and queried using HTTP GET requests.
