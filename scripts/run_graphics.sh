#!/usr/bin/env bash

#----------------------------------------------------------------------
# Run the pygraf graphics for all forecast lead times
#
# Variables provided by Rocoto
#
#  CONFIG_PATH
#  CYCLE
#  IDENTIFIER: text to be printed in title
#
# Variables provided by config
#
#    pygraf_path: path to pygraf clone
#    forecast_length: length of forecast in hours
#    graphics_output_path: path to pygraf output png files
#    image_list: path to the image list YAML file
#    input_data_location: location of input grib files
#    input_file_template: template of grib file name
#    ntasks: number of tasks to use when running pygraf
#    output_interval: the hours between forecast output
#    specs_file: the YAML file defining specs for output figures
#    tiles: the named subregions of input data to plot
#    wait_between_output:  minutes to wait on new output
#    zip_file_path: path to the zip file
#
#----------------------------------------------------------------------


# sourcing yaml section code here is lifted from SRW ush/bash_utils/source_yaml.sh
while read -r line ; do
  # A regex to match list representations
  line=$(echo "$line" | sed -E -e "s/='\[(.*)\]'/=(\1)/" -e 's/,//g' -e 's/"//g' -e 's/None//g')
  source <( echo eval "${line}" )
done < <(uw config realize -i "${CONFIG_PATH}" --output-format sh --key-path graphics.config)


set -x
source $pygraf_path/../../load_wflow_modules.sh $platform
conda activate pygraf
cd $pygraf_path
args=(
  maps
  -d "$input_data_location"
  -f 0 "$forecast_length" "$output_interval"
  --file_type prs
  --file_tmpl "$input_file_template"
  --images "$image_list" hourly
  -m "$IDENTIFIER"
  -n "$ntasks"
  -o "$graphics_output_path"
  -s "$CYCLE"
  --specs "$specs_file"
  --tiles "$tiles"
  -w "$wait_between_output"
  -z "$zip_file_path"
)

python create_graphics.py "${args[@]}"
