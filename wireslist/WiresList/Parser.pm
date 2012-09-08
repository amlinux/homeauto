package WiresList::Parser;

sub new
{
	my $class = shift;
	my $self = {};
	return bless $self, $class;
}

sub parsefile
{
	my $self = shift;
	my $filename = shift;

	my $lineno = 0;
	my $room;
	open my $f, '<', $filename or die "Could not open $filename: $!";
	while (my $line = <$f>) {
		chomp $line;
		$lineno++;
		$line =~ s/^\s*(.*?)\s*$/$1/s;
		next if $line eq '';
		my @tokens = split /\s+/, $line;
		my $cmd = shift @tokens;
		if ($cmd eq 'room') {
			if (@tokens < 2) {
				die "$filename:$lineno: Usage: room <prefix> <name>\n";
			}
			$room = shift @tokens;
			if ($room =~ /-/) {
				die "$filename:$lineno: Dash is not allowed in room code\n";
			}
			if ($self->{roomName}->{$room}) {
				die "$filename:$lineno: Room '$room' is already defined\n";
			}
			$self->{roomName}->{$room} = join(' ', @tokens);
		} elsif ($cmd eq 'area') {
			if (@tokens < 2) {
				die "$filename:$lineno: Usage: area <code> <name>\n";
			}
			if (!$room) {
				die "$filename:$lineno: No 'room' command before 'area'\n";
			}
			my $areaCode = shift @tokens;
			if ($areaCode =~ /-/) {
				die "$filename:$lineno: Dash is not allowed in area code\n";
			}
			my $code = $room . '-' . $areaCode;
			if ($self->{areas}->{$code}) {
				die "$filename:$lineno: Area '$code' is already defined\n";
			}
			$self->{areas}->{$code} = join(' ', @tokens);
		} elsif ($cmd eq 'cable') {
			my $length;
			if (@tokens > 0 && $tokens[-1] =~ /^\d+m$/) {
				$length = pop @tokens;
				$length =~ s/m$//;
			}
			if (@tokens < 5) {
				die "$filename:$lineno: Usage: cable <code> <shortName> <cableType> <area1> <area2> ... [<length>m]\n";
			}
			my $code = shift @tokens;
			my $shortName = shift @tokens;
			my $cableType = shift @tokens;
			if ($self->{cables}->{$code}) {
				die "$filename:$lineno: Cable '$code' is already defined\n";
			}
			for my $area (@tokens) {
				if (!$self->{areas}->{$area}) {
					die "$filename:$lineno: Area '$area' is not defined\n";
				}
				push @{$self->{areaCables}->{$area}}, $code;
			}
			$self->{cables}->{$code} = {
				shortName => $shortName,
				cableType => $cableType,
				areas => \@tokens,
				length => $length,
			};
		} else {
			die "$filename:$lineno: Unknown command: $cmd\n";
		}
	}
	close $f;
}

sub compare
{
	my $code1 = shift;
	my $code2 = shift;
	my @tokens1 = split /-/, $code1;
	my @tokens2 = split /-/, $code2;
	while (@tokens1 && @tokens2) {
		my $t1 = shift @tokens1;
		my $t2 = shift @tokens2;
		if ($t1 =~ /^\d+$/ && $t2 =~ /^\d+$/) {
			my $cmp = $t1 <=> $t2;
			return $cmp if $cmp;
		} else {
			my $cmp = $t1 cmp $t2;
			return $cmp if $cmp;
		}
	}
	return -1 if @tokens1;
	return 1 if @tokens2;
	return 0;
}

sub areas
{
	my $self = shift;
	return map { WiresList::Parser::Area->new($self, $_) } sort { compare($a, $b) } keys %{$self->{areas}};
}

sub cables
{
	my $self = shift;
	return map { WiresList::Parser::Cable->new($self, $_) } sort { compare($a, $b) } keys %{$self->{cables}};
}

sub rooms
{
	my $self = shift;
	return map { WiresList::Parser::Room->new($self, $_) } sort { compare($a, $b) } keys %{$self->{roomName}};
}

package WiresList::Parser::Area;

sub new
{
	my $class = shift;
	my $parser = shift;
	my $code = shift;
	my $self = {
		parser => $parser,
		code => $code,
	};
	return bless $self, $class;
}

sub code
{
	my $self = shift;
	return $self->{code};
}

sub name
{
	my $self = shift;
	return $self->{parser}->{areas}->{$self->{code}};
}

sub cables
{
	my $self = shift;
	return map {
		WiresList::Parser::Cable->new($self->{parser}, $_)
	} sort {
		WiresList::Parser::compare($a, $b);
	} @{$self->{parser}->{areaCables}->{$self->{code}}};
}

sub room
{
	my $self = shift;
	my ($room) = split /-/, $self->{code};
	return WiresList::Parser::Room->new($self->{parser}, $room);
}

package WiresList::Parser::Cable;

sub new
{
	my $class = shift;
	my $parser = shift;
	my $code = shift;
	my $self = {
		parser => $parser,
		code => $code,
	};
	return bless $self, $class;
}

sub code
{
	my $self = shift;
	return $self->{code};
}

sub shortName
{
	my $self = shift;
	return $self->{parser}->{cables}->{$self->{code}}->{shortName};
}

sub cableType
{
	my $self = shift;
	return $self->{parser}->{cables}->{$self->{code}}->{cableType};
}

sub length
{
	my $self = shift;
	return $self->{parser}->{cables}->{$self->{code}}->{length};
}

sub areas
{
	my $self = shift;
	return map {
		WiresList::Parser::Area->new($self->{parser}, $_)
	} @{$self->{parser}->{cables}->{$self->{code}}->{areas}};
}

package WiresList::Parser::Room;

sub new
{
	my $class = shift;
	my $parser = shift;
	my $code = shift;
	my $self = {
		parser => $parser,
		code => $code,
	};
	return bless $self, $class;
}

sub code
{
	my $self = shift;
	return $self->{code};
}

sub name
{
	my $self = shift;
	return $self->{parser}->{roomName}->{$self->{code}};
}

1;
