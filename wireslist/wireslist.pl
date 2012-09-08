#!/usr/bin/perl

use strict;
use lib ($0 =~ /^(.*)\//) ? $1 : '.';
use WiresList::Parser;
use Getopt::Long;

my $hideLength = 0;
my ($input, $output);
my $cablesByRoom = 0;
my $hideAreas = 0;
my $result = GetOptions(
	"hide-length" => \$hideLength,
	"input=s" => \$input,
	"output=s" => \$output,
	"cables-by-room" => \$cablesByRoom,
	"hide-areas" => \$hideAreas,
) or die "Errors parsing command line\n";

if (!$input || !$output) {
	die "Usage: $0 --input <inputfile.conn> --output <outputfile.txt>\n";
}

my $parser = WiresList::Parser->new;
$parser->parsefile($input);

open my $f, '>', $output or die "Could not open $output for writing: $!\n";

print $f qq|<!doctype html><html><head><meta charset=utf-8><title>Разводка кабелей</title><style type="text/css">
body { font-size: 10pt }
h3 { font-size: 12pt; margin: 5px 0 5px 0 }
h2 { font-size: 14pt; margin: 5px 0 5px 0 }
h1 { font-size: 26pt; margin: 5px 0 5px 0 }
ul { margin: 0 }
.section { page-break-after: always }
</style></head><body>\n|;

if (!$hideAreas) {
	my @areas = $parser->areas;
	print $f qq|<div class="section"><h1>Список выводов (| . scalar(@areas) . qq| шт)</h1>\n|;
	my $lastRoom;
	for my $area (@areas) {
		my $room = $area->room->name;
		if ($lastRoom ne $room) {
			print $f "</ul>\n" if $lastRoom;
			print $f "<h2>$room</h2><ul>\n";
			$lastRoom = $room;
		}
		print $f "<li><h3>Точка " . $area->code . ' <span style="color: #808080">(' . $room . " / " . $area->name . ")</span></h3><ul>\n";
		for my $cable ($area->cables) {
			print $f "<li>" . $cable->code . " (кабель " . $cable->cableType . ")";
			my @other;
			for my $a ($cable->areas) {
				if ($a->{code} ne $area->{code}) {
					push @other, $a;
				}
			}
			if (@other) {
				print $f ' <span style="color: #808080">&mdash; соединение с ' . join(', ', map { $_->code } @other) . '</span>';
			}
			print $f "</li>\n";
		}
		print $f "</ul></li>\n";
	}
	print $f "</ul>\n" if $lastRoom;
	print $f "</div>\n";
}

my @cables = $parser->cables;
my $length = 0;
my %lengthByType;
for my $cable (@cables) {
	$length += $cable->length;
	$lengthByType{$cable->cableType} += $cable->length;
}
if ($cablesByRoom) {
	my %roomCables;
	for my $cable (@cables) {
		my %added;
		for my $area ($cable->areas) {
			my $room = $area->room;
			unless ($added{$area->code}++) {
				push @{$roomCables{$room->code}->{cables}}, $cable;
			}
		}
	}
	for my $room ($parser->rooms) {
		my $roomCables = $roomCables{$room->code} or next;
		print $f qq|<div class="section">\n|;
		print $f "<h1>" . $room->name . "</h1>\n";
		my %cableShown;
		for my $cable (@{$roomCables->{cables}}) {
			next if $cableShown{$cable->code}++;
			print $f "<h2>Кабель " . $cable->code . ' <span style="color: #808080">(тип ' . $cable->cableType . ")</span></h2><ul>\n";
			for my $area ($cable->areas) {
				my $ent;
				if ($area->room->code eq $room->code) {
					$ent = qq|<li style="margin: 4px 0 4px 0"><b><span style="border: solid 1px #808080; margin: 1px 3px 1px 0px; padding: 1px 3px 1px 3px">| . $area->code . "</span> " . $area->name . "</b></li>";
				} else {
			       		$ent = qq|<li style="margin: 4px 0 4px 0"><span style="padding: 1px 6px 1px 6px">| . $area->code . "</span> " . $area->room->name . " / " . $area->name . "</li>";
				}
				print $f "$ent\n";
			}
			print $f "</ul>\n";
		}
		print $f "</div>\n";
	}
} else {
	print $f qq|<div class="section"><h1>Список кабелей (" . scalar(@cables) . " шт" . ($hideLength ? '' : ", ${length} м") . ")</h1>\n|;
	for my $cable (@cables) {
		print $f "<h2>Кабель " . $cable->code . ' <span style="color: #808080">(тип ' . $cable->cableType . (($cable->length && !$hideLength) ? ', длина ' . $cable->length . " м" : '') . ")</span></h2><ul>\n";
		for my $area ($cable->areas) {
			print $f "<li>" . $area->code . " (" . $area->room->name . " / " . $area->name . ")</li>\n";
		}
		print $f "</ul>\n";
	}
	print $f "</div>\n";
}

unless ($hideLength) {
	print $f qq|<div class="section"><h1>Итого расход кабеля</h1><ul>\n|;
	for my $type (sort keys %lengthByType) {
		print $f "<li><b>$type</b> &mdash; $lengthByType{$type} м</li>\n";
	}
	print $f qq|</ul></div>\n|;
}

print $f "</body></html>\n";

close $f;

