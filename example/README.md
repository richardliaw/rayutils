Try out this with the following commands:

`ray create_or_update test.yaml -y`

`ray2 setup test.yaml`

To login to the head:
`$(ray2 login_cmd test.yaml)`

To run anything interesting:
`ray2 submit test.yaml [--background] [--shutdown] test.py hi no alsf`
