help([[
This module loads python environement for running the MPAS App on 
the NOAA RDHPC machine Jet 
]]) 
 
whatis([===[Loads libraries needed for running the MPAS App on Jet ]===]) 
 
load("rocoto") 
 
load("conda") 

if mode() == "load" then
   LmodMsgRaw([===[Please do the following to activate conda:
       > conda activate mpas_app
]===])
end
