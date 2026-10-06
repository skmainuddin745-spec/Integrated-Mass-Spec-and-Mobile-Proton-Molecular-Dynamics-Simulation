# Load the required VMD package
package require mdff

# Load the structure file
mol new G:/cytochrome/cytochrome/1/md.gro type gro waitfor all

# Load the trajectory file
mol addfile G:/cytochrome/cytochrome/1/md_noPBC.xtc type xtc waitfor all

# Define the output file for SASA values
set output_file "G:/cytochrome/cytochrome/1/sasa_output.txt"

# Open the output file
set outfile [open $output_file w]

# Write the header to the output file
puts $outfile "Frame\tSASA"

# Loop over all frames in the trajectory
set num_frames [molinfo top get numframes]
for {set frame 0} {$frame < $num_frames} {incr frame} {
    # Set the current frame
    animate goto $frame

    # Calculate the SASA for the current frame
    set sasa [measure sasa 1.4]

    # Write the frame number and SASA to the output file
    puts $outfile "$frame\t$sasa"
}

# Close the output file
close $outfile

# Quit VMD
quit
