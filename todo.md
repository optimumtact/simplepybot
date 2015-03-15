Move the authentication control commands to a seperate module, much the same as how ident has an ident control module.

Why? Right now authentication commands use ident to convert from nickname to nickhost (which is what authentication stores and uses under the hood), if we move that dependence to a seperate module then auth and ident will not depend on each other (just the control modules, which can be loaded as a standard module)


