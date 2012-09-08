#!/usr/bin/perl

use strict;
use lib ($0 =~ /^(.*)\//) ? $1 : '.';
use WiresList::Parser;
use Getopt::Long;

my ($input, $output);
my $result = GetOptions(
	"input=s" => \$input,
	"output=s" => \$output
) or die "Errors parsing command line\n";

if (!$input || !$output) {
	die "Usage: $0 --input <inputfile.conn> --output <outputfile.csv>\n";
}

my $parser = WiresList::Parser->new;
$parser->parsefile($input);

open my $f, '>', $output or die "Could not open $output for writing: $!\n";

for my $cable ($parser->cables) {
	for my $area ($cable->areas) {
		print $f $cable->code . "\n";
	}
}

close $f;
