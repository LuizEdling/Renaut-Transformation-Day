<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class GroupOfThree extends Model
{
    use HasFactory;

    protected $table = 'group_of_three';

    protected $fillable = [
        'cube_1',
        'cube_2',
        'cube_3',
        'group_time',
    ];

    public function cubes()
    {
        return $this->hasMany(Cube::class, 'group_id');
    }
}
