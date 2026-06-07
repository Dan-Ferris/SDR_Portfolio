IQ and FFT theory

what is an iq sample
when your hackrf recieves a radio signal it doesnt just give you a simple number it gives you two numbers 
I = in phase compnoent 
Q = quadrature component

together they form a complex number which is hwy you saw things like (0.003 +0.00j)
when we ran the saopysdr script that j means imaginary its just the q component 

think of it like coordinates on a map
I is your X postion
Q is your Y position
together they describe where the signal is at that exact moment in time 

why two numbers instead of one?
one number can only tell you the amplitude (how strong is the signal is)
two numbers tell you both the amplitude and the Phase (where the signal is in cycle)
that extra information what lets you decode FM, AM digit signal, etc...

What is FFT
FFT stands for Fast Fourier Trasnform 
when your harckrf gives you iq samples that data is in the time domain meaning its just a stream of numbers over time 
you can't easliy tell what frequencies are presetn just by looing at raw numbers
the FFT converst that time domain data into frequency domain 
meaning it tells you exactly which frequencies are present and how strong each one is

think of it like this 
time domain - youre listening to a full band playing music you just hear one combined sound
frequency domain - the FFT separates it out and tells you exactly how loud each instrument is 

thats literally what a spectrum display does 
it runs FFT continoulsy and draws the result on screen